from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ChatType

from app.constants import (
    SUGGEST_BUTTON,
    PROFILE_BUTTON,
    TOURNAMENTS_BUTTON,
    FEEDBACK_BUTTON,
    SEARCH_USER_BUTTON,
    CREATE_TOURNAMENT_BUTTON,
    MANAGE_TOURNAMENTS_BUTTON,
    MUTED_LIST_BUTTON,
    BANNED_LIST_BUTTON,
    ASSIGN_ROLE_BUTTON,
    MOD_STATS_BUTTON,
)
from app.utils import (
    add_user,
    get_admins,
    get_moderators,
    record_message,
    record_sent,
    cleanup,
)
from app.config import Config

router = Router()

_config: Config


def get_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    """Return menu keyboard appropriate for the user."""
    if user_id == _config.admin_id:
        return main_admin_kb
    if user_id in get_admins():
        return admin_kb
    if user_id in get_moderators():
        return moderator_kb
    return menu_kb


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
        [KeyboardButton(text=SEARCH_USER_BUTTON)],
        [KeyboardButton(text=MOD_STATS_BUTTON)],
    ],
    resize_keyboard=True,
)

moderator_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=MUTED_LIST_BUTTON), KeyboardButton(text=BANNED_LIST_BUTTON)],
        [KeyboardButton(text=MOD_STATS_BUTTON)],
    ],
    resize_keyboard=True,
)

main_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=CREATE_TOURNAMENT_BUTTON)],
        [KeyboardButton(text=MANAGE_TOURNAMENTS_BUTTON)],
        [KeyboardButton(text=MUTED_LIST_BUTTON), KeyboardButton(text=BANNED_LIST_BUTTON)],
        [KeyboardButton(text=ASSIGN_ROLE_BUTTON)],
        [KeyboardButton(text=SEARCH_USER_BUTTON)],
        [KeyboardButton(text=MOD_STATS_BUTTON)],
    ],
    resize_keyboard=True,
)


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def handle_start(message: types.Message):
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    add_user(message.from_user)
    user_id = message.from_user.id
    kb = get_menu_kb(user_id)
    if kb is main_admin_kb:
        text = "\U0001F4DD Главное меню администратора"
    elif kb is admin_kb:
        text = "\U0001F4DD Меню администратора"
    elif kb is moderator_kb:
        text = "\U0001F4DD Меню модератора"
    else:
        text = (
            "\U0001F44B Здравствуйте! Нажмите \"Предложить контент\", чтобы отправить материал на модерацию, \"Профиль\" для просмотра статистики или \"Турниры\" для участия."
        )

    sent = await message.answer(text, reply_markup=kb)
    record_sent(sent)
