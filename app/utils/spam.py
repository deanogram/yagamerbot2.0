from datetime import datetime
import re
import time

from .moderation import get_banned_words, get_banned_links

# Maximum number of messages a user can send per day
# Includes proposals, feedback and any other text input
MAX_MESSAGES_PER_DAY = 10
MIN_INTERVAL_SEC = 3
FLOOD_MESSAGE_COUNT = 5
FLOOD_TIME_WINDOW = 10  # seconds
MAX_CAPS_RATIO = 0.9
MIN_EMOJI_COUNT = 3

EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAD6\U0001F600-\U0001F6FF]")

user_stats: dict[int, dict] = {}


def _load_banned_words() -> set[str]:
    return get_banned_words()


def _load_banned_links() -> set[str]:
    return get_banned_links()


def _count_emojis(text: str) -> int:
    return len(EMOJI_RE.findall(text))


def check_message_allowed(user_id: int, text: str) -> tuple[bool, str | None]:
    """Verify spam limits and filter content."""
    data = user_stats.get(user_id)
    now = time.time()
    today = datetime.utcnow().date()

    if data is None or data.get("day") != today:
        data = {
            "count": 0,
            "last_time": 0.0,
            "day": today,
            "timestamps": [],
            "last_text": "",
        }
        user_stats[user_id] = data

    if now - data["last_time"] < MIN_INTERVAL_SEC:
        return False, "Пожалуйста, не спамьте. Подождите немного."

    if data["count"] >= MAX_MESSAGES_PER_DAY:
        return False, "Превышен лимит сообщений на сегодня."

    timestamps = data["timestamps"]
    timestamps.append(now)
    while len(timestamps) > FLOOD_MESSAGE_COUNT:
        timestamps.pop(0)
    if (
        len(timestamps) == FLOOD_MESSAGE_COUNT
        and now - timestamps[0] <= FLOOD_TIME_WINDOW
    ):
        return False, "Флуд: слишком много сообщений подряд."

    if text == data.get("last_text") and text:
        return False, "Повторяющийся контент."

    letters = [ch for ch in text if ch.isalpha()]
    if letters:
        caps_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
        emoji_count = _count_emojis(text)
        if caps_ratio >= MAX_CAPS_RATIO and emoji_count >= MIN_EMOJI_COUNT:
            return False, "Слишком много капса и эмодзи."

    text_lower = (text or "").lower()

    for word in _load_banned_words():
        if word in text_lower:
            return False, "Сообщение содержит запрещенные слова."

    for link in _load_banned_links():
        if link in text_lower:
            return False, "Сообщение содержит запрещенные ссылки."

    data["count"] += 1
    data["last_time"] = now
    data["last_text"] = text
    return True, None
