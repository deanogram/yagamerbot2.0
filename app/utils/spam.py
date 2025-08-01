from datetime import datetime
import time

from .moderation import get_banned_words, get_banned_links

# Maximum number of messages a user can send per day
# Includes proposals, feedback and any other text input
MAX_MESSAGES_PER_DAY = 10
MIN_INTERVAL_SEC = 3

user_stats: dict[int, dict] = {}


def _load_banned_words() -> set[str]:
    return get_banned_words()


def _load_banned_links() -> set[str]:
    return get_banned_links()


def check_message_allowed(user_id: int, text: str) -> tuple[bool, str | None]:
    """Verify spam limits and filter content."""
    data = user_stats.get(user_id)
    now = time.time()
    today = datetime.utcnow().date()

    if data is None or data.get("day") != today:
        data = {"count": 0, "last_time": 0.0, "day": today}
        user_stats[user_id] = data

    if now - data["last_time"] < MIN_INTERVAL_SEC:
        return False, "Пожалуйста, не спамьте. Подождите немного."

    if data["count"] >= MAX_MESSAGES_PER_DAY:
        return False, "Превышен лимит сообщений на сегодня."

    text_lower = (text or "").lower()

    for word in _load_banned_words():
        if word in text_lower:
            return False, "Сообщение содержит запрещенные слова."

    for link in _load_banned_links():
        if link in text_lower:
            return False, "Сообщение содержит запрещенные ссылки."

    data["count"] += 1
    data["last_time"] = now
    return True, None
