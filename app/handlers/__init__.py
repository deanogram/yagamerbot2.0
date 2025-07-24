from aiogram import Dispatcher

from app.config import Config
from . import start, suggest, misc, profile, tournaments


def register_handlers(dp: Dispatcher, config: Config) -> None:
    dp.include_router(start.router)
    suggest.setup(config)
    dp.include_router(suggest.router)
    dp.include_router(profile.router)
    dp.include_router(tournaments.router)
    dp.include_router(misc.router)
