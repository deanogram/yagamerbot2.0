from aiogram import types, Router
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from .suggest import SUGGEST_BUTTON

router = Router()


menu_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=SUGGEST_BUTTON)]],
    resize_keyboard=True,
)


@router.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Отправьте мне сообщение, и оно будет переслано модераторам.",
        reply_markup=menu_kb,
    )
