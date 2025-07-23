from aiogram import Dispatcher

from app.config import Config
from . import start, suggest, misc


def register_handlers(dp: Dispatcher, config: Config) -> None:
    dp.include_router(start.router)
    suggest.setup(config)
    dp.include_router(suggest.router)
    misc.setup(config)
    dp.include_router(misc.router)
