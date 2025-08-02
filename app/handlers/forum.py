from aiogram import Router, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command
import time

from app.config import Config
from app.utils import (
    add_user,
    add_xp,
    add_warning,
    get_warnings,
    clear_warnings,
    mute_user,
    unmute_user,
    is_muted,
)
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
    if (
        event.new_chat_member.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED}
        and event.old_chat_member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}
    ):
        user = event.new_chat_member.user
        if user.is_bot:
            await event.bot.ban_chat_member(event.chat.id, user.id)
            return
        add_user(user)
        try:
            await event.bot.send_message(
                event.chat.id,
                f"Добро пожаловать, {user.full_name}!",
            )
        except Exception:
            pass


@router.message(lambda m: m.chat.id == _config.forum_chat_id)
async def moderate_group_message(message: types.Message) -> None:
    if is_muted(message.from_user.id):
        await message.delete()
        return

    allowed, reason = check_message_allowed(
        message.from_user.id, message.text or message.caption or ""
    )
    if not allowed:
        await message.delete()
        user = message.from_user
        if user.username:
            mention = f"@{user.username}"
        else:
            mention = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'

        if reason in {
            "Сообщение содержит запрещенные слова.",
            "Сообщение содержит запрещенные ссылки.",
            "Флуд: слишком много сообщений подряд.",
            "Повторяющийся контент.",
            "Слишком много капса и эмодзи.",
        }:
            count = add_warning(message.from_user.id)
            if count >= 4:
                mute_user(message.from_user.id, 24 * 3600)
                clear_warnings(message.from_user.id)
                try:
                    await message.bot.restrict_chat_member(
                        _config.forum_chat_id,
                        message.from_user.id,
                        types.ChatPermissions(can_send_messages=False),
                        until_date=int(time.time()) + 24 * 3600,
                    )
                    await message.bot.send_message(
                        message.chat.id,
                        f"{mention} получил мут на 24 часа за нарушения.",
                        parse_mode="HTML",
                    )
                    await message.bot.send_message(
                        message.from_user.id,
                        "Вы получили мут на 24 часа за нарушения.",
                    )
                except Exception:
                    pass
            else:
                if reason.startswith("Сообщение содержит запрещенные слова"):
                    warn_text = "Ай ай ай, приятель, не стоит выражаться"
                elif reason == "Флуд: слишком много сообщений подряд.":
                    warn_text = "Не флуди в чате, пожалуйста"
                elif reason == "Повторяющийся контент.":
                    warn_text = "Не отправляй одно и то же сообщение снова"
                elif reason == "Слишком много капса и эмодзи.":
                    warn_text = "Не злоупотребляй капсом и эмодзи"
                else:
                    warn_text = "Тут нельзя ничего рекламировать, друг"
                try:
                    text = f"{warn_text} ({count}/3 варнов)"
                    await message.bot.send_message(
                        message.chat.id,
                        f"{mention} {text}",
                        parse_mode="HTML",
                    )
                    try:
                        await message.bot.send_message(message.from_user.id, text)
                    except Exception:
                        pass
                except Exception:
                    pass
        else:
            try:
                await message.bot.send_message(
                    message.chat.id,
                    f"{mention} {reason}",
                    parse_mode="HTML",
                )
                try:
                    await message.bot.send_message(message.from_user.id, reason)
                except Exception:
                    pass
            except Exception:
                pass
        return
    add_user(message.from_user)
    add_xp(message.from_user.id, 1)


def _allowed_staff(message: types.Message) -> bool:
    return (
        message.from_user.id == _config.admin_id
        or message.chat.id == _config.mod_chat_id
    )


@router.message(Command("mute"))
async def cmd_mute(message: types.Message) -> None:
    if not _allowed_staff(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /mute <user_id> [hours]")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.reply("Invalid user id")
        return
    hours = int(parts[2]) if len(parts) > 2 else 24
    mute_user(user_id, hours * 3600)
    try:
        await message.bot.restrict_chat_member(
            _config.forum_chat_id,
            user_id,
            types.ChatPermissions(can_send_messages=False),
            until_date=int(time.time()) + hours * 3600,
        )
        await message.reply(f"User {user_id} muted for {hours}h")
    except Exception:
        await message.reply("Failed to mute user")


@router.message(Command("unmute"))
async def cmd_unmute(message: types.Message) -> None:
    if not _allowed_staff(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /unmute <user_id>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.reply("Invalid user id")
        return
    unmute_user(user_id)
    try:
        await message.bot.restrict_chat_member(
            _config.forum_chat_id,
            user_id,
            types.ChatPermissions(can_send_messages=True),
        )
        await message.reply("User unmuted")
    except Exception:
        await message.reply("Failed to unmute user")


@router.message(Command("ban"))
async def cmd_ban(message: types.Message) -> None:
    if not _allowed_staff(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /ban <user_id>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.reply("Invalid user id")
        return
    try:
        await message.bot.ban_chat_member(_config.forum_chat_id, user_id)
        await message.reply("User banned")
    except Exception:
        await message.reply("Failed to ban user")


@router.message(Command("unban"))
async def cmd_unban(message: types.Message) -> None:
    if not _allowed_staff(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /unban <user_id>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.reply("Invalid user id")
        return
    try:
        await message.bot.unban_chat_member(_config.forum_chat_id, user_id)
        await message.reply("User unbanned")
    except Exception:
        await message.reply("Failed to unban user")


@router.message(Command("warnings"))
async def cmd_warnings(message: types.Message) -> None:
    if not _allowed_staff(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /warnings <user_id>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.reply("Invalid user id")
        return
    count = get_warnings(user_id)
    await message.reply(f"Warnings: {count}")


@router.message(Command("clearwarn"))
async def cmd_clearwarn(message: types.Message) -> None:
    if not _allowed_staff(message):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /clearwarn <user_id>")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.reply("Invalid user id")
        return
    clear_warnings(user_id)
    await message.reply("Warnings cleared")

