from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.utils.spam import check_message_allowed
from app.utils import add_user, increment_submission, record_result
from app.config import Config
from app.constants import SUGGEST_BUTTON, BACK_BUTTON
from . import start

router = Router()

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BACK_BUTTON)]],
    resize_keyboard=True,
)


class Suggest(StatesGroup):
    waiting_for_content = State()


suggestions: dict[int, dict] = {}
waiting_comments: dict[int, int] = {}

_config: Config | None = None

def setup(config: Config):
    global _config
    _config = config


@router.message(Command("suggest"))
@router.message(F.text == SUGGEST_BUTTON)
async def cmd_suggest(message: types.Message, state: FSMContext):
    add_user(message.from_user)
    await state.set_state(Suggest.waiting_for_content)
    await message.answer(
        "Отправьте контент (фото, видео, текст, гиф или музыку) для модерации.",
        reply_markup=cancel_kb,
    )


@router.message(Suggest.waiting_for_content, F.text == BACK_BUTTON)
async def cancel_suggest(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню", reply_markup=start.get_menu_kb(message.from_user.id))


@router.message(Suggest.waiting_for_content)
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

    mod_message = await message.send_copy(
        _config.mod_chat_id,
        reply_markup=kb,
    )

    add_user(message.from_user)
    increment_submission(message.from_user.id)

    suggestions[mod_message.message_id] = {
        "user_id": message.chat.id,
        "decision": None,
    }

    await message.answer(
        "Контент отправлен на модерацию.",
        reply_markup=start.get_menu_kb(message.from_user.id),
    )
    await state.clear()


@router.callback_query(F.data.in_({"approve", "reject"}))
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

    await callback.bot.send_message(
        _config.mod_chat_id,
        "Оставьте комментарий для пользователя или нажмите 'Пропустить'.",
        reply_markup=skip_kb,
    )
    await callback.answer("Решение сохранено. Ожидаю комментарий.")


@router.message(lambda message: message.chat.id == _config.mod_chat_id)
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

    await message.bot.send_message(entry["user_id"], answer)
    record_result(entry["user_id"], decision)
    waiting_comments.pop(message.from_user.id, None)
    await message.reply("Ответ отправлен пользователю.")


@router.callback_query(F.data == "skip")
async def skip_comment(callback: types.CallbackQuery):
    mod_msg_id = waiting_comments.pop(callback.from_user.id, None)
    entry = suggestions.pop(mod_msg_id, None) if mod_msg_id else None
    if not entry:
        await callback.answer()
        return

    decision = entry["decision"] == "approve"
    text = "Ваш контент принят!" if decision else "Ваш контент отклонен."
    await callback.bot.send_message(entry["user_id"], text)
    record_result(entry["user_id"], decision)
    await callback.answer("Ответ отправлен пользователю.")
