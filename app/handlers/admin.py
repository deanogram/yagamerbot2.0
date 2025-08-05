from aiogram import Router, types, F, Bot
import time
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
    SEARCH_USER_BUTTON,
    MOD_STATS_BUTTON,
    PARTICIPANTS_LIST_BUTTON,
    BACK_BUTTON,
    LEVEL_BEGINNER_BUTTON,
    LEVEL_AMATEUR_BUTTON,
    LEVEL_PRO_BUTTON,
)
from . import start
from app.utils import (
    get_all_user_ids,
    add_tournament,
    update_tournament,
    delete_tournament,
    get_tournaments,
    get_participants,
    remove_participant,
    get_all_mutes,
    get_all_bans,
    unmute_user,
    unban_user,
    get_user_by_username,
    set_user_title,
    add_xp,
    mute_user,
    ban_user,
    is_muted,
    is_banned,
    add_admin,
    add_moderator,
    get_admins,
    get_moderators,
    get_user_stats,
    get_strikes,
    clear_strikes,
    get_mod_stats,
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

level_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=LEVEL_BEGINNER_BUTTON)],
        [KeyboardButton(text=LEVEL_AMATEUR_BUTTON)],
        [KeyboardButton(text=LEVEL_PRO_BUTTON)],
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
    waiting_level = State()
    waiting_type = State()
    waiting_date = State()
    waiting_prize = State()
    waiting_preview = State()


class TournamentEdit(StatesGroup):
    waiting_game = State()
    waiting_level = State()
    waiting_type = State()
    waiting_date = State()
    waiting_prize = State()
    waiting_preview = State()


class UserEdit(StatesGroup):
    waiting_title = State()
    waiting_xp = State()
    waiting_mute = State()
    waiting_ban = State()


class UserSearch(StatesGroup):
    waiting_query = State()


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
    """Return menu keyboard for admin or moderator."""
    return start.get_menu_kb(user_id)


def _user_edit_kb(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Изменить титул", callback_data=f"set_title:{user_id}")],
        [
            InlineKeyboardButton(text="Добавить XP", callback_data=f"addxp:{user_id}"),
            InlineKeyboardButton(text="Отнять XP", callback_data=f"subxp:{user_id}"),
        ],
    ]
    if is_muted(user_id):
        buttons.append([InlineKeyboardButton(text="Размутить", callback_data=f"unmute:{user_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="Мут", callback_data=f"muteuser:{user_id}")])
    if is_banned(user_id):
        buttons.append([InlineKeyboardButton(text="Разбанить", callback_data=f"unban:{user_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="Бан", callback_data=f"banuser:{user_id}")])
    buttons.append([InlineKeyboardButton(text="Страйки", callback_data=f"strikes:{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _send_user_menu(bot: Bot, chat_id: int, user_id: int) -> None:
    stats = get_user_stats(user_id) or {}
    text = (
        f"ID: {user_id}\n"
        f"Username: @{stats.get('username') or 'нет'}\n"
        f"XP: {stats.get('xp', 0)}\n"
        f"Титул: {stats.get('title') or '-'}"
    )
    await bot.send_message(chat_id, text, reply_markup=_user_edit_kb(user_id))


@router.message(Command("modstats"))
@router.message(F.text == MOD_STATS_BUTTON)
async def mod_stats(message: types.Message) -> None:
    if not _is_staff(message.from_user.id):
        return
    stats = get_mod_stats()
    top = "\n".join(
        f"{i+1}. {uid} — {count}" for i, (uid, count) in enumerate(stats["top_offenders"])
    )
    if not top:
        top = "нет"
    text = (
        f"Предупреждений за сутки: {stats['warnings_24h']}\n"
        f"Мутов/банов за сутки: {stats['mutes_bans_24h']}\n"
        f"Топ-нарушителей:\n{top}"
    )
    await message.answer(text, reply_markup=_menu_kb(message.from_user.id))


@router.message(Command("user"))
async def find_user(message: types.Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Usage: /user <id|@username>")
        return
    query = parts[1].strip()
    if query.startswith("@"):  # username search
        stats = get_user_by_username(query[1:])
    elif query.isdigit():
        stats = get_user_stats(int(query))
    else:
        stats = get_user_by_username(query)
    if not stats:
        await message.reply("User not found")
        return
    await _send_user_menu(message.bot, message.chat.id, stats["user_id"])


@router.message(F.text == SEARCH_USER_BUTTON)
async def ask_search_query(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    await message.answer("Введите ID или username", reply_markup=cancel_kb)
    await state.set_state(UserSearch.waiting_query)


@router.message(UserSearch.waiting_query, F.text == BACK_BUTTON)
async def cancel_search(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню", reply_markup=_menu_kb(message.from_user.id))


@router.message(UserSearch.waiting_query)
async def process_search(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return
    query = message.text.strip()
    if query.startswith("@"):  # username search
        stats = get_user_by_username(query[1:])
    elif query.isdigit():
        stats = get_user_stats(int(query))
    else:
        stats = get_user_by_username(query)
    await state.clear()
    if not stats:
        await message.answer("User not found", reply_markup=_menu_kb(message.from_user.id))
        return
    await _send_user_menu(message.bot, message.chat.id, stats["user_id"])


@router.message(
    TournamentCreate.waiting_game,
    F.text == BACK_BUTTON,
)
@router.message(TournamentCreate.waiting_level, F.text == BACK_BUTTON)
@router.message(TournamentCreate.waiting_type, F.text == BACK_BUTTON)
@router.message(TournamentCreate.waiting_date, F.text == BACK_BUTTON)
@router.message(TournamentCreate.waiting_prize, F.text == BACK_BUTTON)
@router.message(TournamentCreate.waiting_preview, F.text == BACK_BUTTON)
async def cancel_create(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню", reply_markup=_menu_kb(message.from_user.id))


@router.message(TournamentEdit.waiting_game, F.text == BACK_BUTTON)
@router.message(TournamentEdit.waiting_level, F.text == BACK_BUTTON)
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
async def choose_level(message: types.Message, state: FSMContext) -> None:
    await state.update_data(game=message.text)
    await state.set_state(TournamentCreate.waiting_level)
    await message.answer("\U0001F3C5 Выберите уровень", reply_markup=level_kb)


@router.message(TournamentCreate.waiting_level)
async def choose_type(message: types.Message, state: FSMContext) -> None:
    await state.update_data(level=message.text)
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
        data.get("level"),
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
    for tid, game, level, type_, date, prize, preview in tournaments:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Редактировать", callback_data=f"edit_tour:{tid}")],
                [InlineKeyboardButton(text="Удалить", callback_data=f"del_tour:{tid}")],
                [InlineKeyboardButton(text=PARTICIPANTS_LIST_BUTTON, callback_data=f"list_part:{tid}")],
            ]
        )
        text = f"{tid}. {game} ({level}) {type_} — {date}, призовой фонд: {prize}"
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
    for user_id, _ in entries:
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
async def edit_choose_level(message: types.Message, state: FSMContext) -> None:
    await state.update_data(game=message.text)
    await state.set_state(TournamentEdit.waiting_level)
    await message.answer("\U0001F3C5 Выберите уровень", reply_markup=level_kb)


@router.message(TournamentEdit.waiting_level)
async def edit_choose_type(message: types.Message, state: FSMContext) -> None:
    await state.update_data(level=message.text)
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
        data.get("level"),
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


@router.callback_query(F.data.startswith("list_part:"))
async def cb_list_participants(callback: types.CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    tid = int(callback.data.split(":", 1)[1])
    entries = get_participants(tid)
    if not entries:
        await callback.answer("Список пуст", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer("\U0001F4CB Участники:")
    for user_id, nickname, age in entries:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Исключить", callback_data=f"kick_part:{tid}:{user_id}")]
            ]
        )
        stats = get_user_stats(user_id)
        username = f"@{stats.get('username')}" if stats and stats.get('username') else "нет"
        await callback.message.answer(f"{nickname} ({age}) — {username}", reply_markup=kb)


@router.callback_query(F.data.startswith("kick_part:"))
async def cb_kick_participant(callback: types.CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    _, tid, uid = callback.data.split(":")
    remove_participant(int(tid), int(uid))
    await callback.answer("Исключен")
    await callback.message.edit_text("Исключен")


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


@router.callback_query(F.data.startswith("edit_user:"))
async def cb_edit_user(callback: types.CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    await callback.answer()
    await _send_user_menu(callback.bot, callback.message.chat.id, uid)


@router.callback_query(F.data.startswith("set_title:"))
async def cb_set_title(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    await state.update_data(edit_uid=uid)
    await state.set_state(UserEdit.waiting_title)
    await callback.message.answer("Введите новый титул (или '-' чтобы удалить)")
    await callback.answer()


@router.message(UserEdit.waiting_title)
async def process_title(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    uid = data.get("edit_uid")
    title = message.text.strip()
    if title == "-":
        title = ""
    set_user_title(uid, title)
    await state.clear()
    await message.answer("Титул обновлен")
    await _send_user_menu(message.bot, message.chat.id, uid)


@router.callback_query(F.data.startswith("addxp:"))
async def cb_add_xp(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    await state.update_data(edit_uid=uid, xp_sign=1)
    await state.set_state(UserEdit.waiting_xp)
    await callback.message.answer("Введите количество XP для добавления")
    await callback.answer()


@router.callback_query(F.data.startswith("subxp:"))
async def cb_sub_xp(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    await state.update_data(edit_uid=uid, xp_sign=-1)
    await state.set_state(UserEdit.waiting_xp)
    await callback.message.answer("Введите количество XP для вычета")
    await callback.answer()


@router.message(UserEdit.waiting_xp)
async def process_xp(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    uid = data.get("edit_uid")
    sign = data.get("xp_sign", 1)
    try:
        amount = int(message.text)
    except ValueError:
        await message.answer("Нужно число")
        return
    add_xp(uid, amount * sign)
    await state.clear()
    await message.answer("XP изменено")
    await _send_user_menu(message.bot, message.chat.id, uid)


@router.callback_query(F.data.startswith("muteuser:"))
async def cb_mute_user(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    await state.update_data(edit_uid=uid)
    await state.set_state(UserEdit.waiting_mute)
    await callback.message.answer("На сколько часов выдать мут? (0 - навсегда)")
    await callback.answer()


@router.message(UserEdit.waiting_mute)
async def process_mute(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    uid = data.get("edit_uid")
    try:
        hours = int(message.text)
    except ValueError:
        await message.answer("Нужно число")
        return
    mute_user(uid, hours * 3600 if hours > 0 else 0, moderator_id=message.from_user.id, reason="admin")
    await state.clear()
    await message.answer("Мут установлен")
    await message.bot.send_message(
        _config.mod_chat_id,
        f"🔇 User {uid} muted for {hours}h by {message.from_user.id}",
    )
    await _send_user_menu(message.bot, message.chat.id, uid)


@router.callback_query(F.data.startswith("banuser:"))
async def cb_ban_user(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    await state.update_data(edit_uid=uid)
    await state.set_state(UserEdit.waiting_ban)
    await callback.message.answer("На сколько часов бан? (0 - навсегда)")
    await callback.answer()


@router.message(UserEdit.waiting_ban)
async def process_ban(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    uid = data.get("edit_uid")
    try:
        hours = int(message.text)
    except ValueError:
        await message.answer("Нужно число")
        return
    ban_user(uid, hours * 3600 if hours > 0 else 0, moderator_id=message.from_user.id, reason="admin")
    try:
        await message.bot.ban_chat_member(_config.forum_chat_id, uid, until_date=int(time.time()) + hours * 3600 if hours > 0 else None)
    except Exception:
        pass
    await state.clear()
    await message.answer("Бан установлен")
    await message.bot.send_message(
        _config.mod_chat_id,
        f"⛔ User {uid} banned for {hours}h by {message.from_user.id}",
    )
    await _send_user_menu(message.bot, message.chat.id, uid)


@router.callback_query(F.data.startswith("strikes:"))
async def cb_strikes(callback: types.CallbackQuery) -> None:
    if not _is_staff(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    count = get_strikes(uid)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сбросить", callback_data=f"clearstrikes:{uid}")],
            [InlineKeyboardButton(text="Назад", callback_data=f"userback:{uid}")],
        ]
    )
    await callback.message.answer(f"Страйки: {count}", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("clearstrikes:"))
async def cb_clear_strikes(callback: types.CallbackQuery) -> None:
    if not _is_staff(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    clear_strikes(uid)
    await callback.message.answer("Страйки сброшены")
    await _send_user_menu(callback.bot, callback.message.chat.id, uid)
    await callback.answer()


@router.callback_query(F.data.startswith("userback:"))
async def cb_user_back(callback: types.CallbackQuery) -> None:
    if not _is_staff(callback.from_user.id):
        await callback.answer()
        return
    uid = int(callback.data.split(":", 1)[1])
    await _send_user_menu(callback.bot, callback.message.chat.id, uid)
    await callback.answer()


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

