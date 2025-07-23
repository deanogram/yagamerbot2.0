import asyncio
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime
import time
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

# данные для антиспама
MAX_MESSAGES_PER_DAY = 20
MIN_INTERVAL_SEC = 3

user_stats: dict[int, dict] = {}
banned_words = {"spam", "junk", "badword"}


def check_message_allowed(user_id: int, text: str) -> tuple[bool, str | None]:
    """Verify spam limits and filter content."""
    data = user_stats.get(user_id)
    now = time.time()
    today = datetime.utcnow().date()

    if data is None or data.get("day") != today:
        data = {"count": 0, "last_time": 0.0, "day": today}
        user_stats[user_id] = data

    if now - data["last_time"] < MIN_INTERVAL_SEC:
        return False, "Пожалуйста, не спамьте. Подождите немного."

    if data["count"] >= MAX_MESSAGES_PER_DAY:
        return False, "Превышен лимит сообщений на сегодня."

    text_lower = (text or "").lower()
    for word in banned_words:
        if word in text_lower:
            return False, "Сообщение содержит запрещенные слова."

    data["count"] += 1
    data["last_time"] = now
    return True, None

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

    allowed, reason = check_message_allowed(
        message.chat.id, message.text or message.caption or ""
    )
    if not allowed:
        await message.answer(reason)
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
        allowed, reason = check_message_allowed(
            message.chat.id, message.text or message.caption or ""
        )
        if not allowed:
            await message.answer(reason)
            return
        await bot.forward_message(MOD_CHAT_ID, message.chat.id, message.message_id)
        await message.answer("Ваше сообщение отправлено модераторам.")
    else:
        await message.answer("Пожалуйста, пишите боту в личные сообщения.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
