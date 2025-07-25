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
        "\U0001F3C1 Добро пожаловать в турнирную ЯGAMER. Участвуй и побеждай!",
        reply_markup=tournament_kb,
    )


@router.message(F.text == BACK_BUTTON)
async def tournaments_back(message: types.Message) -> None:
    await message.answer("Главное меню", reply_markup=start.menu_kb)


@router.message(F.text == JOIN_BUTTON)
async def show_tournaments(message: types.Message) -> None:
    tournaments = get_tournaments()
    if not tournaments:
        await message.answer("\u2753 Турниры не запланированы")
        return
    await message.answer("\U0001F4C5 Актуальные турниры:")
    for tid, game, type_, date, prize, preview in tournaments:
        text = f"{tid}. {game} {type_} — {date}, призовой фонд: {prize}"
        if preview:
            await message.bot.send_photo(message.chat.id, preview, caption=text)
        else:
            await message.answer(text)


@router.message(F.text == RATING_BUTTON)
async def show_rating(message: types.Message) -> None:
    ratings = get_tournament_ratings()
    if not ratings:
        await message.answer("\u2753 Рейтинг пока пуст.")
        return

    lines = ["\U0001F3C6 Рейтинг игроков:"]
    for rank, name, score in ratings:
        lines.append(f"{rank}. {name} — {score}")
    await message.answer("\n".join(lines))
