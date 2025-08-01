from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.utils import (
    get_tournament_ratings,
    get_tournaments,
    get_tournament,
    add_participant,
    record_tournament,
    record_message,
    record_sent,
    cleanup,
)
from app.constants import (
    TOURNAMENTS_BUTTON,
    JOIN_BUTTON,
    RATING_BUTTON,
    SIGNUP_BUTTON,
    BACK_BUTTON,
)
from . import start

router = Router()


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BACK_BUTTON)]],
    resize_keyboard=True,
)


class JoinState(StatesGroup):
    waiting_nick = State()
    waiting_age = State()


tournament_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=JOIN_BUTTON)],
        [KeyboardButton(text=RATING_BUTTON)],
        [KeyboardButton(text=BACK_BUTTON)],
    ],
    resize_keyboard=True,
)


@router.message(Command("tournaments"))
@router.message(F.text == TOURNAMENTS_BUTTON)
async def tournaments_menu(message: types.Message) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    sent = await message.answer(
        "\U0001F3C1 Добро пожаловать в турнирную ЯGAMER. Участвуй и побеждай!",
        reply_markup=tournament_kb,
    )
    record_sent(sent)


@router.message(F.text == BACK_BUTTON)
async def tournaments_back(message: types.Message) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    sent = await message.answer("Главное меню", reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)


@router.message(F.text == JOIN_BUTTON)
async def show_tournaments(message: types.Message) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    tournaments = get_tournaments()
    if not tournaments:
        sent = await message.answer("\u2753 Турниры не запланированы")
        record_sent(sent)
        return
    sent = await message.answer("\U0001F4C5 Актуальные турниры:")
    record_sent(sent)
    for tid, game, level, type_, date, prize, preview in tournaments:
        text = f"{tid}. {game} ({level}) {type_} — {date}, призовой фонд: {prize}"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=SIGNUP_BUTTON, callback_data=f"join_tour:{tid}")]
            ]
        )
        if preview:
            sent_photo = await message.bot.send_photo(message.chat.id, preview, caption=text, reply_markup=kb)
            record_sent(sent_photo)
        else:
            sent_msg = await message.answer(text, reply_markup=kb)
            record_sent(sent_msg)


@router.message(F.text == RATING_BUTTON)
async def show_rating(message: types.Message) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    ratings = get_tournament_ratings()
    if not ratings:
        sent = await message.answer(
            "\u2753 Рейтинг пока пуст.", reply_markup=tournament_kb
        )
        record_sent(sent)
        return

    lines = ["\U0001F3C6 Рейтинг игроков:"]
    for rank, name, score in ratings:
        lines.append(f"{rank}. {name} — {score}")
    sent = await message.answer("\n".join(lines), reply_markup=tournament_kb)
    record_sent(sent)


@router.callback_query(F.data.startswith("join_tour:"))
async def cb_join_tournament(callback: types.CallbackQuery, state: FSMContext) -> None:
    await cleanup(callback.bot, callback.message.chat.id)
    tid = int(callback.data.split(":", 1)[1])
    await state.update_data(tid=tid)
    await state.set_state(JoinState.waiting_nick)
    sent = await callback.message.answer("Введите ваш никнейм", reply_markup=cancel_kb)
    record_sent(sent)
    await callback.answer()


@router.message(JoinState.waiting_nick, F.text == BACK_BUTTON)
@router.message(JoinState.waiting_age, F.text == BACK_BUTTON)
async def cancel_join(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    await state.clear()
    sent = await message.answer("Главное меню", reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)


@router.message(JoinState.waiting_nick)
async def ask_age(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    await state.update_data(nickname=message.text)
    await state.set_state(JoinState.waiting_age)
    sent = await message.answer("Введите ваш возраст", reply_markup=cancel_kb)
    record_sent(sent)


@router.message(JoinState.waiting_age)
async def save_participant(message: types.Message, state: FSMContext) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    data = await state.get_data()
    try:
        age = int(message.text)
    except ValueError:
        sent = await message.answer("Возраст должен быть числом. Попробуйте снова.")
        record_sent(sent)
        return
    added = add_participant(
        data.get("tid"),
        message.from_user.id,
        data.get("nickname"),
        age,
    )
    if added:
        tour = get_tournament(data.get("tid"))
        if tour:
            _, game, level, type_, date, *_ = tour
            text = f"Вы записаны на турнир {game} ({level}) {type_} — {date}!"
        else:
            text = "Вы записаны на турнир!"
        sent = await message.answer(text, reply_markup=start.get_menu_kb(message.from_user.id))
        record_sent(sent)
        new_ach = record_tournament(message.from_user.id)
        for ach in new_ach:
            sent_a = await message.answer(f"Получено достижение: {ach}!")
            record_sent(sent_a)
    else:
        sent = await message.answer("Вы уже записаны на этот турнир.", reply_markup=start.get_menu_kb(message.from_user.id))
        record_sent(sent)
    await state.clear()
