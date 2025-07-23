import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import load_config, Config
from app.handlers import register_handlers

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    config: Config = load_config()
    bot = Bot(config.bot_token)
    dp = Dispatcher()

    register_handlers(dp, config)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
