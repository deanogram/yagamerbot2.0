from aiogram import types, Router
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.constants import (
    SUGGEST_BUTTON,
    PROFILE_BUTTON,
    TOURNAMENTS_BUTTON,
    FEEDBACK_BUTTON,
    CREATE_TOURNAMENT_BUTTON,
    MANAGE_TOURNAMENTS_BUTTON,
    MUTED_LIST_BUTTON,
    BANNED_LIST_BUTTON,
    ASSIGN_ROLE_BUTTON,
)
from app.utils import add_user, get_admins, get_moderators
from app.config import Config

router = Router()

_config: Config


def setup(config: Config) -> None:
    global _config
    _config = config


menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=SUGGEST_BUTTON),
            KeyboardButton(text=PROFILE_BUTTON),
        ],
        [KeyboardButton(text=TOURNAMENTS_BUTTON)],
        [KeyboardButton(text=FEEDBACK_BUTTON)],
    ],
    resize_keyboard=True,
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=CREATE_TOURNAMENT_BUTTON)],
        [KeyboardButton(text=MANAGE_TOURNAMENTS_BUTTON)],
        [KeyboardButton(text=MUTED_LIST_BUTTON), KeyboardButton(text=BANNED_LIST_BUTTON)],
    ],
    resize_keyboard=True,
)

moderator_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MUTED_LIST_BUTTON), KeyboardButton(text=BANNED_LIST_BUTTON)],
    ],
    resize_keyboard=True,
)

main_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=CREATE_TOURNAMENT_BUTTON)],
        [KeyboardButton(text=MANAGE_TOURNAMENTS_BUTTON)],
        [KeyboardButton(text=MUTED_LIST_BUTTON), KeyboardButton(text=BANNED_LIST_BUTTON)],
        [KeyboardButton(text=ASSIGN_ROLE_BUTTON)],
    ],
    resize_keyboard=True,
)


@router.message(CommandStart())
async def handle_start(message: types.Message):
    add_user(message.from_user)
    user_id = message.from_user.id
    if user_id == _config.admin_id:
        kb = main_admin_kb
        text = "\U0001F4DD Главное меню администратора"
    elif user_id in get_admins():
        kb = admin_kb
        text = "\U0001F4DD Меню администратора"
    elif user_id in get_moderators():
        kb = moderator_kb
        text = "\U0001F4DD Меню модератора"
    else:
        kb = menu_kb
        text = (
            "\U0001F44B Здравствуйте! Нажмите \"Предложить контент\", чтобы отправить материал на модерацию, \"Профиль\" для просмотра статистики или \"Турниры\" для участия."
        )

    await message.answer(text, reply_markup=kb)
