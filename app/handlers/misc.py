from aiogram import types, Router
from aiogram.enums import ChatType

from app.utils.spam import check_message_allowed
from app.config import Config

router = Router()

_config: Config | None = None

def setup(config: Config):
    global _config
    _config = config


@router.message()
async def forward_private(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        allowed, reason = check_message_allowed(
            message.chat.id, message.text or message.caption or ""
        )
        if not allowed:
            await message.answer(reason)
            return
        await message.bot.forward_message(_config.mod_chat_id, message.chat.id, message.message_id)
        await message.answer("Ваше сообщение отправлено модераторам.")
    else:
        await message.answer("Пожалуйста, пишите боту в личные сообщения.")
