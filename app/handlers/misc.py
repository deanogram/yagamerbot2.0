from aiogram import types, Router
from aiogram.enums import ChatType

router = Router()


@router.message()
async def prompt_suggest(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.answer(
            "Нажмите \"Предложить контент\", чтобы отправить материал на модерацию."
        )
    else:
        await message.answer("Пожалуйста, пишите боту в личные сообщения.")
