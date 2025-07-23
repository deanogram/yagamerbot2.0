from aiogram import types, Router
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Отправьте мне сообщение, и оно будет переслано модераторам."
    )
