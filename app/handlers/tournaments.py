from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.utils import get_tournament_ratings, get_tournaments
from app.constants import (
    TOURNAMENTS_BUTTON,
    JOIN_BUTTON,
    RATING_BUTTON,
    BACK_BUTTON,
)
from . import start

router = Router()


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
    await message.answer(
        "Добро пожаловать в турнирную ЯGAMER. Участвуй, побеждай и получи удовольствие!",
        reply_markup=tournament_kb,
    )


@router.message(F.text == BACK_BUTTON)
async def tournaments_back(message: types.Message) -> None:
    await message.answer("Главное меню", reply_markup=start.menu_kb)


@router.message(F.text == JOIN_BUTTON)
async def show_tournaments(message: types.Message) -> None:
    tournaments = get_tournaments()
    if not tournaments:
        await message.answer("Турниры не запланированы")
        return
    lines = ["Актуальные турниры:"]
    for tid, game, type_, date, prize in tournaments:
        lines.append(f"{tid}. {game} {type_} — {date}, призовой фонд: {prize}")
    await message.answer("\n".join(lines))


@router.message(F.text == RATING_BUTTON)
async def show_rating(message: types.Message) -> None:
    ratings = get_tournament_ratings()
    if not ratings:
        await message.answer("Рейтинг пока пуст.")
        return

    lines = ["Рейтинг игроков:"]
    for rank, name, score in ratings:
        lines.append(f"{rank}. {name} — {score}")
    await message.answer("\n".join(lines))
