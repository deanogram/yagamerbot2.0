from datetime import datetime
import time

MAX_MESSAGES_PER_DAY = 20
MIN_INTERVAL_SEC = 3

user_stats: dict[int, dict] = {}
banned_words = {"spam", "junk", "badword"}


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
    for word in banned_words:
        if word in text_lower:
            return False, "Сообщение содержит запрещенные слова."

    data["count"] += 1
    data["last_time"] = now
    return True, None
