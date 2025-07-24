from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.utils import get_tournament_ratings

router = Router()

TOURNAMENTS_BUTTON = "\U0001F3C6 Турниры"
JOIN_BUTTON = "Участвовать"
RATING_BUTTON = "Рейтинг игроков"


tournament_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=JOIN_BUTTON)],
        [KeyboardButton(text=RATING_BUTTON)],
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


@router.message(F.text == JOIN_BUTTON)
async def show_tournaments(message: types.Message) -> None:
    text = (
        "Актуальные турниры:\n"
        "- CS2\n"
        "- Dota 2\n"
        "- Valorant"
    )
    await message.answer(text)


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
