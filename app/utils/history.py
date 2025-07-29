from collections import defaultdict
from aiogram import Bot, types
from aiogram.enums import ChatType

_message_history: dict[int, list[int]] = defaultdict(list)


def record_message(message: types.Message) -> None:
    """Remember a message to remove later."""
    if message.chat.type != ChatType.PRIVATE:
        return
    _message_history[message.chat.id].append(message.message_id)


def record_sent(message: types.Message) -> None:
    """Remember a bot reply to remove later."""
    if message.chat.type != ChatType.PRIVATE:
        return
    _message_history[message.chat.id].append(message.message_id)


async def cleanup(bot: Bot, chat_id: int) -> None:
    """Delete stored messages for chat."""
    ids = _message_history.pop(chat_id, [])
    for mid in ids:
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass
