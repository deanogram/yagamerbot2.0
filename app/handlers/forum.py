from aiogram import Router, types
from aiogram.enums import ChatMemberStatus

from app.config import Config
from app.utils import add_user, add_xp
from app.utils.spam import check_message_allowed

router = Router()
_config: Config


def setup(config: Config) -> None:
    global _config
    _config = config


@router.chat_member()
async def handle_new_member(event: types.ChatMemberUpdated) -> None:
    if event.chat.id != _config.forum_chat_id:
        return
    if event.new_chat_member.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED}:
        user = event.from_user
        if user.is_bot:
            await event.bot.ban_chat_member(event.chat.id, user.id)
            return
        add_user(user)


@router.message(lambda m: m.chat.id == _config.forum_chat_id)
async def moderate_group_message(message: types.Message) -> None:
    allowed, reason = check_message_allowed(message.from_user.id, message.text or message.caption or "")
    if not allowed:
        await message.delete()
        try:
            await message.bot.send_message(message.from_user.id, reason)
        except Exception:
            pass
        return
    add_user(message.from_user)
    add_xp(message.from_user.id, 1)

