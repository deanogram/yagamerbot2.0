from aiogram import types, Router
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from .suggest import SUGGEST_BUTTON
from .profile import PROFILE_BUTTON
from app.utils import add_user

router = Router()


menu_kb = ReplyKeyboardMarkup(
    keyboard=[[
        KeyboardButton(text=SUGGEST_BUTTON),
        KeyboardButton(text=PROFILE_BUTTON),
    ]],
    resize_keyboard=True,
)


@router.message(CommandStart())
async def handle_start(message: types.Message):
    add_user(message.from_user)
    await message.answer(
        "Здравствуйте! Нажмите \"Предложить контент\", чтобы отправить материал на модерацию, или \"Профиль\" для просмотра статистики.",
        reply_markup=menu_kb,
    )
