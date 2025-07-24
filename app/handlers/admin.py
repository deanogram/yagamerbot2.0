from aiogram import Router, types, F
from aiogram.filters import Command

from app.config import Config
from app.utils import get_all_user_ids

router = Router()
_config: Config


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

