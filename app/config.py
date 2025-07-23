from dataclasses import dataclass
import os
from dotenv import load_dotenv

@dataclass
class Config:
    bot_token: str
    admin_id: int
    mod_chat_id: int


def load_config() -> 'Config':
    load_dotenv()
    return Config(
        bot_token=os.getenv("BOT_TOKEN", ""),
        admin_id=int(os.getenv("ADMIN_ID", 0)),
        mod_chat_id=int(os.getenv("MOD_CHAT_ID", 0)),
    )
