from aiogram import Router, types, F
from aiogram.filters import Command

from app.utils import add_user, get_user_stats, get_warnings
from app.constants import PROFILE_BUTTON
from . import start

router = Router()


def get_rank(xp: int) -> str:
    if xp <= 500:
        return "Новичок"
    if xp <= 1000:
        return "Джун"
    if xp <= 2000:
        return "Бывалый"
    if xp <= 5000:
        return "Pro"
    return "Легенда"


@router.message(Command("profile"))
@router.message(F.text == PROFILE_BUTTON)
async def handle_profile(message: types.Message) -> None:
    add_user(message.from_user)
    stats = get_user_stats(message.from_user.id) or {}
    xp = stats.get("xp", 0)
    warnings = get_warnings(message.from_user.id)
    rank = get_rank(xp)

    text = (
        f"Username: @{message.from_user.username or 'нет'}\n"
        f"XP: {xp}\n"
        f"Предупреждений: {warnings}\n"
        f"Ранг: {rank}"
    )
    await message.answer(text, reply_markup=start.get_menu_kb(message.from_user.id))
