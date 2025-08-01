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
from app.utils import (
    add_user,
    increment_submission,
    record_result,
    record_meme,
    record_video,
    record_message,
    record_sent,
    cleanup,
)
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
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    add_user(message.from_user)
    await state.set_state(Suggest.waiting_for_content)
    sent = await message.answer(
        "Отправьте контент (фото, видео, текст, гиф или музыку) для модерации.",
        reply_markup=cancel_kb,
    )
    record_sent(sent)


@router.message(Suggest.waiting_for_content, F.text == BACK_BUTTON)
async def cancel_suggest(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    await state.clear()
    sent = await message.answer("Главное меню", reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)


@router.message(Suggest.waiting_for_content)
async def receive_content(message: types.Message, state: FSMContext):
    if message.chat.type != ChatType.PRIVATE:
        return

    await cleanup(message.bot, message.chat.id)

    allowed, reason = check_message_allowed(
        message.chat.id, message.text or message.caption or ""
    )
    if not allowed:
        sent_err = await message.answer(reason)
        record_sent(sent_err)
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="approve"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data="reject"),
            ]
        ]
    )

    if message.video or message.video_note:
        ctype = "video"
    else:
        ctype = "meme"

    mod_message = await message.send_copy(
        _config.mod_chat_id,
        reply_markup=kb,
    )

    add_user(message.from_user)
    increment_submission(message.from_user.id)

    suggestions[mod_message.message_id] = {
        "user_id": message.chat.id,
        "decision": None,
        "type": ctype,
    }

    sent2 = await message.answer(
        "Контент отправлен на модерацию.",
        reply_markup=start.get_menu_kb(message.from_user.id),
    )
    record_sent(sent2)
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

    sent = await callback.bot.send_message(
        _config.mod_chat_id,
        "Оставьте комментарий для пользователя или нажмите 'Пропустить'.",
        reply_markup=skip_kb,
    )
    record_sent(sent)
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

    sent = await message.bot.send_message(entry["user_id"], answer)
    record_sent(sent)
    record_result(entry["user_id"], decision)
    if decision:
        if entry.get("type") == "video":
            new_ach = record_video(entry["user_id"])
        else:
            new_ach = record_meme(entry["user_id"])
        for ach in new_ach:
            sent_a = await message.bot.send_message(entry["user_id"], f"Получено достижение: {ach}!")
            record_sent(sent_a)
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
    sent = await callback.bot.send_message(entry["user_id"], text)
    record_sent(sent)
    record_result(entry["user_id"], decision)
    if decision:
        if entry.get("type") == "video":
            new_ach = record_video(entry["user_id"])
        else:
            new_ach = record_meme(entry["user_id"])
        for ach in new_ach:
            sent_a = await callback.bot.send_message(entry["user_id"], f"Получено достижение: {ach}!")
            record_sent(sent_a)
    await callback.answer("Ответ отправлен пользователю.")
