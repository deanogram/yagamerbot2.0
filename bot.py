import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ChatType
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
MOD_CHAT_ID = int(os.getenv("MOD_CHAT_ID", 0))

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Отправьте мне сообщение, и оно будет переслано модераторам."
    )

@dp.message()
async def forward_private(message: types.Message):
    if message.chat.type == ChatType.PRIVATE:
        await bot.forward_message(MOD_CHAT_ID, message.chat.id, message.message_id)
        await message.answer("Ваше сообщение отправлено модераторам.")
    else:
        await message.answer("Пожалуйста, пишите боту в личные сообщения.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
