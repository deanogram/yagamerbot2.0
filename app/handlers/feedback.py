from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.constants import (
    FEEDBACK_BUTTON,
    PROPOSAL_BUTTON,
    QUESTION_BUTTON,
    COMPLAINT_BUTTON,
    BACK_BUTTON,
)
from app.utils.spam import check_message_allowed
from app.config import Config
from . import start
from app.utils import record_message, record_sent, cleanup

router = Router()
_config: Config


def setup(config: Config) -> None:
    global _config
    _config = config


feedback_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=PROPOSAL_BUTTON)],
        [KeyboardButton(text=QUESTION_BUTTON)],
        [KeyboardButton(text=COMPLAINT_BUTTON)],
        [KeyboardButton(text=BACK_BUTTON)],
    ],
    resize_keyboard=True,
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BACK_BUTTON)]],
    resize_keyboard=True,
)


class FeedbackState(StatesGroup):
    waiting_proposal = State()
    waiting_question = State()
    waiting_complaint = State()


entries: dict[int, int] = {}


@router.message(Command("feedback"))
@router.message(F.text == FEEDBACK_BUTTON)
async def feedback_menu(message: types.Message) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    sent = await message.answer(
        "\U0001F4AC Есть какие-то идеи по улучшению, жалоба или вопрос? Пиши!",
        reply_markup=feedback_kb,
    )
    record_sent(sent)


@router.message(F.text == BACK_BUTTON)
async def feedback_back(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    await state.clear()
    sent = await message.answer("Главное меню", reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)


@router.message(F.text == PROPOSAL_BUTTON)
async def ask_proposal(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    sent = await message.answer("\U0001F4A1 Что хочешь предложить, приятель?", reply_markup=cancel_kb)
    record_sent(sent)
    await state.set_state(FeedbackState.waiting_proposal)


@router.message(FeedbackState.waiting_proposal, F.text == BACK_BUTTON)
async def cancel_proposal(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    await state.clear()
    sent = await message.answer("Главное меню", reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)


@router.message(FeedbackState.waiting_proposal)
async def handle_proposal(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    allowed, reason = check_message_allowed(message.from_user.id, message.text or "")
    if not allowed:
        sent = await message.answer(reason)
        record_sent(sent)
        return
    mod_msg = await message.bot.send_message(
        _config.feedback_chat_id,
        f"[Предложение]\nОт {message.from_user.full_name} ({message.from_user.id})\n{message.text}",
    )
    entries[mod_msg.message_id] = message.chat.id
    sent = await message.answer(
        "Отправили твоё предложение, спасибо за активность!",
        reply_markup=start.get_menu_kb(message.from_user.id),
    )
    record_sent(sent)
    await state.clear()


@router.message(F.text == QUESTION_BUTTON)
async def ask_question(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    sent = await message.answer("\u2753 Задай свой вопрос", reply_markup=cancel_kb)
    record_sent(sent)
    await state.set_state(FeedbackState.waiting_question)


@router.message(FeedbackState.waiting_question, F.text == BACK_BUTTON)
async def cancel_question(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    await state.clear()
    sent = await message.answer("Главное меню", reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)


@router.message(FeedbackState.waiting_question)
async def handle_question(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    allowed, reason = check_message_allowed(message.from_user.id, message.text or "")
    if not allowed:
        sent = await message.answer(reason)
        record_sent(sent)
        return
    mod_msg = await message.bot.send_message(
        _config.feedback_chat_id,
        f"[Вопрос]\nОт {message.from_user.full_name} ({message.from_user.id})\n{message.text}",
    )
    entries[mod_msg.message_id] = message.chat.id
    sent = await message.answer(
        "Спасибо за вопрос, ответим в скором времени!",
        reply_markup=start.get_menu_kb(message.from_user.id),
    )
    record_sent(sent)
    await state.clear()


@router.message(F.text == COMPLAINT_BUTTON)
async def ask_complaint(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    sent = await message.answer(
        "\U0001F620 Воу воу, приятель, что не так? Расскажи подробнее",
        reply_markup=cancel_kb,
    )
    record_sent(sent)
    await state.set_state(FeedbackState.waiting_complaint)


@router.message(FeedbackState.waiting_complaint, F.text == BACK_BUTTON)
async def cancel_complaint(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    await state.clear()
    sent = await message.answer("Главное меню", reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)


@router.message(FeedbackState.waiting_complaint)
async def handle_complaint(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    allowed, reason = check_message_allowed(message.from_user.id, message.text or "")
    if not allowed:
        sent = await message.answer(reason)
        record_sent(sent)
        return
    mod_msg = await message.bot.send_message(
        _config.feedback_chat_id,
        f"[Жалоба]\nОт {message.from_user.full_name} ({message.from_user.id})\n{message.text}",
    )
    entries[mod_msg.message_id] = message.chat.id
    sent = await message.answer("Всё решим, не волнуйся!", reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)
    await state.clear()


@router.message(lambda m: m.chat.id == _config.feedback_chat_id and m.reply_to_message)
async def moderator_reply(message: types.Message) -> None:
    user_id = entries.get(message.reply_to_message.message_id)
    if not user_id:
        return
    await message.send_copy(user_id)
    await message.reply("Ответ отправлен пользователю.")
