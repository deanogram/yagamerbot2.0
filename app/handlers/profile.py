from aiogram import Router, types, F
from aiogram.filters import Command

from app.utils import (
    add_user,
    get_user_stats,
    get_warnings,
    get_user_achievements,
    record_message,
    record_sent,
    cleanup,
)
from app.constants import PROFILE_BUTTON
from . import start

router = Router()


def get_rank(xp: int) -> str:
    if xp <= 100:
        return "Нубик"
    if xp <= 500:
        return "Новобранец"
    if xp <= 1000:
        return "Бывалый"
    if xp <= 1500:
        return "Pro"
    if xp <= 2000:
        return "Мастер"
    if xp <= 4000:
        return "Грандмастер"
    if xp <= 10000:
        return "Легенда!"
    return "Титан"


@router.message(Command("profile"))
@router.message(F.text == PROFILE_BUTTON)
async def handle_profile(message: types.Message) -> None:
    record_message(message)
    await cleanup(message.bot, message.chat.id)
    add_user(message.from_user)
    stats = get_user_stats(message.from_user.id) or {}
    xp = stats.get("xp", 0)
    title = stats.get("title") or "-"
    warnings = get_warnings(message.from_user.id)
    achievements = get_user_achievements(message.from_user.id)
    rank = get_rank(xp)

    text = (
        f"Username: @{message.from_user.username or 'нет'}\n"
        f"XP: {xp}\n"
        f"Предупреждений: {warnings}\n"
        f"Ранг: {rank}\n"
        f"Титул: {title}"
    )
    if achievements:
        text += "\n\nДостижения:\n" + "\n".join(achievements)
    sent = await message.answer(text, reply_markup=start.get_menu_kb(message.from_user.id))
    record_sent(sent)
