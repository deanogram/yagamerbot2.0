from aiogram import types, Router
from aiogram.enums import ChatType

from app.utils.spam import check_message_allowed

router = Router()


@router.message()
async def prompt_suggest(message: types.Message):
    allowed, reason = check_message_allowed(
        message.from_user.id, message.text or message.caption or ""
    )
    if not allowed:
        await message.answer(reason)
        return

    if message.chat.type == ChatType.PRIVATE:
        await message.answer(
            "Нажмите \"Предложить контент\", чтобы отправить материал на модерацию."
        )
    else:
        await message.answer("Пожалуйста, пишите боту в личные сообщения.")
