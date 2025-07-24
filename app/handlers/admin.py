from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.config import Config
from app.constants import (
    CREATE_TOURNAMENT_BUTTON,
    MUTED_LIST_BUTTON,
    BANNED_LIST_BUTTON,
    ASSIGN_ROLE_BUTTON,
)
from app.utils import (
    get_all_user_ids,
    add_tournament,
    get_all_mutes,
    get_all_bans,
    unmute_user,
    unban_user,
    add_admin,
    add_moderator,
    get_admins,
    get_moderators,
)

router = Router()
_config: Config


class TournamentCreate(StatesGroup):
    waiting_game = State()
    waiting_type = State()
    waiting_date = State()


def setup(config: Config) -> None:
    global _config
    _config = config


@router.message(Command("broadcast"))
async def broadcast(message: types.Message) -> None:
    if message.from_user.id != _config.admin_id:
        return
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        await message.answer("Usage: /broadcast <text>")
        return
    payload = text[1]
    count = 0
    for user_id in get_all_user_ids():
        try:
            await message.bot.send_message(user_id, payload)
            count += 1
        except Exception:
            pass
    await message.answer(f"Рассылка отправлена {count} пользователям.")


def _is_admin(user_id: int) -> bool:
    return user_id == _config.admin_id or user_id in get_admins()


def _is_staff(user_id: int) -> bool:
    return _is_admin(user_id) or user_id in get_moderators()


@router.message(F.text == CREATE_TOURNAMENT_BUTTON)
async def create_tournament_start(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    await state.set_state(TournamentCreate.waiting_game)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="CS2")], [KeyboardButton(text="Dota 2")], [KeyboardButton(text="Valorant")]],
        resize_keyboard=True,
    )
    await message.answer("Выберите игру", reply_markup=kb)


@router.message(TournamentCreate.waiting_game)
async def choose_type(message: types.Message, state: FSMContext) -> None:
    await state.update_data(game=message.text)
    await state.set_state(TournamentCreate.waiting_type)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="1 vs 1")], [KeyboardButton(text="2 vs 2")], [KeyboardButton(text="5 vs 5")]],
        resize_keyboard=True,
    )
    await message.answer("Выберите формат", reply_markup=kb)


@router.message(TournamentCreate.waiting_type)
async def choose_date(message: types.Message, state: FSMContext) -> None:
    await state.update_data(type=message.text)
    await state.set_state(TournamentCreate.waiting_date)
    await message.answer("Введите дату турнира (например, 01.01.2024)")


@router.message(TournamentCreate.waiting_date)
async def save_tournament(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    add_tournament(data.get("game"), data.get("type"), message.text)
    await message.answer("Турнир создан")
    await state.clear()


@router.message(F.text == MUTED_LIST_BUTTON)
async def list_mutes(message: types.Message) -> None:
    if not _is_staff(message.from_user.id):
        return
    entries = get_all_mutes()
    if not entries:
        await message.answer("Список мута пуст")
        return
    for user_id, _ in entries:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Размутить", callback_data=f"unmute:{user_id}")]]
        )
        await message.answer(str(user_id), reply_markup=kb)


@router.message(F.text == BANNED_LIST_BUTTON)
async def list_bans(message: types.Message) -> None:
    if not _is_staff(message.from_user.id):
        return
    entries = get_all_bans()
    if not entries:
        await message.answer("Список банов пуст")
        return
    for user_id in entries:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Разбанить", callback_data=f"unban:{user_id}")]]
        )
        await message.answer(str(user_id), reply_markup=kb)


@router.callback_query(F.data.startswith("unmute:"))
async def cb_unmute(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split(":", 1)[1])
    unmute_user(user_id)
    await callback.answer("Пользователь размучен")
    await callback.message.edit_text("Размучен")


@router.callback_query(F.data.startswith("unban:"))
async def cb_unban(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split(":", 1)[1])
    unban_user(user_id)
    await callback.answer("Пользователь разбанен")
    await callback.message.edit_text("Разбанен")


@router.message(Command("promote"))
async def promote_user(message: types.Message) -> None:
    if message.from_user.id != _config.admin_id:
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("Usage: /promote <user_id> <admin|mod>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.reply("Invalid user id")
        return
    role = parts[2].lower()
    if role == "admin":
        add_admin(user_id)
    elif role == "mod":
        add_moderator(user_id)
    else:
        await message.reply("Role must be admin or mod")
        return
    await message.reply("Пользователь назначен")


@router.message(F.text == ASSIGN_ROLE_BUTTON)
async def assign_help(message: types.Message) -> None:
    if message.from_user.id != _config.admin_id:
        return
    await message.answer("Используйте команду /promote <user_id> <admin|mod>")

