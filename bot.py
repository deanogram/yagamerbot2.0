import asyncio
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
MOD_CHAT_ID = int(os.getenv("MOD_CHAT_ID", 0))

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


class Suggest(StatesGroup):
    waiting_for_content = State()


suggestions: dict[int, dict] = {}
waiting_comments: dict[int, int] = {}

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Отправьте мне сообщение, и оно будет переслано модераторам."
    )


@dp.message(Command("suggest"))
async def cmd_suggest(message: types.Message, state: FSMContext):
    await state.set_state(Suggest.waiting_for_content)
    await message.answer(
        "Отправьте контент (фото, видео, текст, гиф или музыку) для модерации."
    )


@dp.message(Suggest.waiting_for_content)
async def receive_content(message: types.Message, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE:
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="approve"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data="reject"),
            ]
        ]
    )

    mod_message = await bot.copy_message(
        MOD_CHAT_ID,
        message.chat.id,
        message.message_id,
        reply_markup=kb,
    )

    suggestions[mod_message.message_id] = {
        "user_id": message.chat.id,
        "decision": None,
    }

    await message.answer("Контент отправлен на модерацию.")
    await state.clear()


@dp.callback_query(F.data.in_({"approve", "reject"}))
async def moderation_decision(callback: types.CallbackQuery):
    entry = suggestions.get(callback.message.message_id)
    if not entry:
        await callback.answer()
        return

    entry["decision"] = callback.data
    waiting_comments[callback.from_user.id] = callback.message.message_id

    skip_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Пропустить", callback_data="skip")]]
    )

    await bot.send_message(
        MOD_CHAT_ID,
        "Оставьте комментарий для пользователя или нажмите 'Пропустить'.",
        reply_markup=skip_kb,
    )
    await callback.answer("Решение сохранено. Ожидаю комментарий.")


@dp.message(F.chat.id == MOD_CHAT_ID)
async def moderator_comment(message: types.Message):
    mod_msg_id = waiting_comments.get(message.from_user.id)
    if not mod_msg_id:
        return

    entry = suggestions.pop(mod_msg_id, None)
    if not entry:
        waiting_comments.pop(message.from_user.id, None)
        return

    decision = entry["decision"] == "approve"
    text = message.text or ""
    if decision:
        answer = "Ваш контент принят!"
    else:
        answer = "Ваш контент отклонен."
    if text:
        answer += f"\nКомментарий модератора: {text}"

    await bot.send_message(entry["user_id"], answer)
    waiting_comments.pop(message.from_user.id, None)
    await message.reply("Ответ отправлен пользователю.")


@dp.callback_query(F.data == "skip")
async def skip_comment(callback: types.CallbackQuery):
    mod_msg_id = waiting_comments.pop(callback.from_user.id, None)
    entry = suggestions.pop(mod_msg_id, None) if mod_msg_id else None
    if not entry:
        await callback.answer()
        return

    decision = entry["decision"] == "approve"
    text = "Ваш контент принят!" if decision else "Ваш контент отклонен."
    await bot.send_message(entry["user_id"], text)
    await callback.answer("Ответ отправлен пользователю.")

@dp.message()
async def forward_private(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await bot.forward_message(MOD_CHAT_ID, message.chat.id, message.message_id)
        await message.answer("Ваше сообщение отправлено модераторам.")
    else:
        await message.answer("Пожалуйста, пишите боту в личные сообщения.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
