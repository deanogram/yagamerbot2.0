from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.config import Config
from app.constants import (
    CREATE_TOURNAMENT_BUTTON,
    MANAGE_TOURNAMENTS_BUTTON,
    MUTED_LIST_BUTTON,
    BANNED_LIST_BUTTON,
    ASSIGN_ROLE_BUTTON,
    BACK_BUTTON,
)
from . import start
from app.utils import (
    get_all_user_ids,
    add_tournament,
    update_tournament,
    delete_tournament,
    get_tournaments,
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

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BACK_BUTTON)]],
    resize_keyboard=True,
)

game_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="CS2")],
        [KeyboardButton(text="Dota 2")],
        [KeyboardButton(text="Valorant")],
        [KeyboardButton(text=BACK_BUTTON)],
    ],
    resize_keyboard=True,
)

type_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 vs 1")],
        [KeyboardButton(text="2 vs 2")],
        [KeyboardButton(text="5 vs 5")],
        [KeyboardButton(text=BACK_BUTTON)],
    ],
    resize_keyboard=True,
)

preview_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пропустить")],
        [KeyboardButton(text=BACK_BUTTON)],
    ],
    resize_keyboard=True,
)


class TournamentCreate(StatesGroup):
    waiting_game = State()
    waiting_type = State()
    waiting_date = State()
    waiting_prize = State()
    waiting_preview = State()


class TournamentEdit(StatesGroup):
    waiting_game = State()
    waiting_type = State()
    waiting_date = State()
    waiting_prize = State()
    waiting_preview = State()


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


def _menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    """Return appropriate admin menu keyboard."""
    if user_id == _config.admin_id:
        return start.main_admin_kb
    return start.admin_kb


@router.message(
    TournamentCreate.waiting_game,
    F.text == BACK_BUTTON,
)
@router.message(TournamentCreate.waiting_type, F.text == BACK_BUTTON)
@router.message(TournamentCreate.waiting_date, F.text == BACK_BUTTON)
@router.message(TournamentCreate.waiting_prize, F.text == BACK_BUTTON)
@router.message(TournamentCreate.waiting_preview, F.text == BACK_BUTTON)
async def cancel_create(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню", reply_markup=_menu_kb(message.from_user.id))


@router.message(TournamentEdit.waiting_game, F.text == BACK_BUTTON)
@router.message(TournamentEdit.waiting_type, F.text == BACK_BUTTON)
@router.message(TournamentEdit.waiting_date, F.text == BACK_BUTTON)
@router.message(TournamentEdit.waiting_prize, F.text == BACK_BUTTON)
@router.message(TournamentEdit.waiting_preview, F.text == BACK_BUTTON)
async def cancel_edit(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню", reply_markup=_menu_kb(message.from_user.id))


@router.message(F.text == BACK_BUTTON)
async def admin_back(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("Главное меню", reply_markup=_menu_kb(message.from_user.id))




@router.message(F.text == CREATE_TOURNAMENT_BUTTON)
async def create_tournament_start(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    await state.set_state(TournamentCreate.waiting_game)
    await message.answer("\U0001F3AE Выберите игру", reply_markup=game_kb)


@router.message(TournamentCreate.waiting_game)
async def choose_type(message: types.Message, state: FSMContext) -> None:
    await state.update_data(game=message.text)
    await state.set_state(TournamentCreate.waiting_type)
    await message.answer("\U0001F4DD Выберите формат", reply_markup=type_kb)


@router.message(TournamentCreate.waiting_type)
async def choose_date(message: types.Message, state: FSMContext) -> None:
    await state.update_data(type=message.text)
    await state.set_state(TournamentCreate.waiting_date)
    await message.answer(
        "\U0001F4C5 Введите дату турнира (например, 01.01.2024)",
        reply_markup=cancel_kb,
    )


@router.message(TournamentCreate.waiting_date)
async def ask_prize(message: types.Message, state: FSMContext) -> None:
    await state.update_data(date=message.text)
    await state.set_state(TournamentCreate.waiting_prize)
    await message.answer("\U0001F4B0 Введите призовой фонд", reply_markup=cancel_kb)


@router.message(TournamentCreate.waiting_prize)
async def ask_preview(message: types.Message, state: FSMContext) -> None:
    await state.update_data(prize=message.text)
    await state.set_state(TournamentCreate.waiting_preview)
    await message.answer(
        "Отправьте фото-превью турнира или нажмите 'Пропустить'",
        reply_markup=preview_kb,
    )


@router.message(TournamentCreate.waiting_preview)
async def save_tournament(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    add_tournament(
        data.get("game"),
        data.get("type"),
        data.get("date"),
        data.get("prize"),
        message.photo[-1].file_id if message.photo else None if message.text == "Пропустить" else message.text,
    )
    await message.answer(
        "\u2705 Турнир создан",
        reply_markup=_menu_kb(message.from_user.id),
    )
    await state.clear()


@router.message(F.text == MANAGE_TOURNAMENTS_BUTTON)
async def manage_tournaments(message: types.Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    tournaments = get_tournaments()
    if not tournaments:
        await message.answer("Турниры не запланированы", reply_markup=cancel_kb)
        return
    await message.answer("\U0001F4C5 Список турниров:", reply_markup=cancel_kb)
    for tid, game, type_, date, prize, preview in tournaments:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Редактировать", callback_data=f"edit_tour:{tid}")],
                [InlineKeyboardButton(text="Удалить", callback_data=f"del_tour:{tid}")],
            ]
        )
        text = f"{tid}. {game} {type_} — {date}, призовой фонд: {prize}"
        if preview:
            await message.bot.send_photo(message.chat.id, preview, caption=text, reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb)


@router.message(F.text == MUTED_LIST_BUTTON)
async def list_mutes(message: types.Message) -> None:
    if not _is_staff(message.from_user.id):
        return
    entries = get_all_mutes()
    if not entries:
        await message.answer("Список мута пуст", reply_markup=cancel_kb)
        return
    await message.answer("\U0001F910 Замученные пользователи:", reply_markup=cancel_kb)
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
        await message.answer("Список банов пуст", reply_markup=cancel_kb)
        return
    await message.answer("\u26D4\ufe0f Забаненные пользователи:", reply_markup=cancel_kb)
    for user_id in entries:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Разбанить", callback_data=f"unban:{user_id}")]]
        )
        await message.answer(str(user_id), reply_markup=kb)


@router.callback_query(F.data.startswith("edit_tour:"))
async def cb_edit_tournament(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    tid = int(callback.data.split(":", 1)[1])
    await state.update_data(edit_id=tid)
    await state.set_state(TournamentEdit.waiting_game)
    await callback.message.answer("\U0001F3AE Выберите игру", reply_markup=game_kb)
    await callback.answer()


@router.message(TournamentEdit.waiting_game)
async def edit_choose_type(message: types.Message, state: FSMContext) -> None:
    await state.update_data(game=message.text)
    await state.set_state(TournamentEdit.waiting_type)
    await message.answer("\U0001F4DD Выберите формат", reply_markup=type_kb)


@router.message(TournamentEdit.waiting_type)
async def edit_choose_date(message: types.Message, state: FSMContext) -> None:
    await state.update_data(type=message.text)
    await state.set_state(TournamentEdit.waiting_date)
    await message.answer(
        "\U0001F4C5 Введите дату турнира (например, 01.01.2024)",
        reply_markup=cancel_kb,
    )


@router.message(TournamentEdit.waiting_date)
async def edit_ask_prize(message: types.Message, state: FSMContext) -> None:
    await state.update_data(date=message.text)
    await state.set_state(TournamentEdit.waiting_prize)
    await message.answer("\U0001F4B0 Введите призовой фонд", reply_markup=cancel_kb)


@router.message(TournamentEdit.waiting_prize)
async def edit_ask_preview(message: types.Message, state: FSMContext) -> None:
    await state.update_data(prize=message.text)
    await state.set_state(TournamentEdit.waiting_preview)
    await message.answer(
        "Отправьте новое фото-превью или нажмите 'Пропустить'",
        reply_markup=preview_kb,
    )


@router.message(TournamentEdit.waiting_preview)
async def save_edit(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    update_tournament(
        data.get("edit_id"),
        data.get("game"),
        data.get("type"),
        data.get("date"),
        data.get("prize"),
        message.photo[-1].file_id if message.photo else None if message.text == "Пропустить" else message.text,
    )
    await message.answer(
        "\u2705 Турнир обновлен",
        reply_markup=_menu_kb(message.from_user.id),
    )
    await state.clear()


@router.callback_query(F.data.startswith("del_tour:"))
async def cb_delete_tournament(callback: types.CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    tid = int(callback.data.split(":", 1)[1])
    delete_tournament(tid)
    await callback.answer("Турнир удален")
    await callback.message.edit_text("Удален")


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

