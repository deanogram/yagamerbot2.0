from aiogram import Router, types, F
from aiogram.filters import Command

from app.utils import add_user, get_user_stats
from app.constants import PROFILE_BUTTON
from . import start

router = Router()


@router.message(Command("profile"))
@router.message(F.text == PROFILE_BUTTON)
async def handle_profile(message: types.Message) -> None:
    add_user(message.from_user)
    stats = get_user_stats(message.from_user.id) or {}
    xp = stats.get("xp", 0)
    total = stats.get("sent_total", 0)
    approved = stats.get("sent_approved", 0)
    rejected = stats.get("sent_rejected", 0)

    text = (
        f"Имя: {message.from_user.full_name}\n"
        f"Username: @{message.from_user.username or 'нет'}\n"
        f"XP: {xp}\n"
        f"Отправлено контента: {total}\n"
        f"\u2705 Принято: {approved}\n"
        f"\u274C Отклонено: {rejected}"
    )
    await message.answer(text, reply_markup=start.menu_kb)
