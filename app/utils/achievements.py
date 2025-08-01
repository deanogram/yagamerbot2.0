import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "achievements.db"


ACHIEVEMENTS = {
    "memodel": {
        "name": "Мемодел",
        "emoji": "\U0001F5BC",  # framed picture
        "field": "memes",
        "threshold": 50,
    },
    "contentmaker": {
        "name": "Контентмейкер",
        "emoji": "\U0001F39E",  # film frames
        "field": "videos",
        "threshold": 50,
    },
    "fighter": {
        "name": "Боец",
        "emoji": "\u2694\ufe0f",  # crossed swords
        "field": "tournaments",
        "threshold": 10,
    },
    "gladiator": {
        "name": "Гладиатор",
        "emoji": "\U0001F6E1",  # shield
        "field": "tournaments",
        "threshold": 50,
    },
}


def init_achievements_db() -> None:
    """Create tables for achievement progress and awards."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                user_id INTEGER PRIMARY KEY,
                memes INTEGER DEFAULT 0,
                videos INTEGER DEFAULT 0,
                tournaments INTEGER DEFAULT 0
            )
            """,
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER,
                achievement TEXT,
                PRIMARY KEY (user_id, achievement)
            )
            """,
        )
        conn.commit()


def _add_achievement(conn: sqlite3.Connection, user_id: int, name: str, emoji: str) -> bool:
    """Store achievement for user if not present. Return True if added."""
    ach = f"{emoji} {name}"
    cur = conn.execute(
        "SELECT 1 FROM user_achievements WHERE user_id=? AND achievement=?",
        (user_id, ach),
    )
    if cur.fetchone():
        return False
    conn.execute(
        "INSERT INTO user_achievements(user_id, achievement) VALUES(?, ?)",
        (user_id, ach),
    )
    return True


def _increment(user_id: int, field: str) -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            f"""INSERT INTO progress(user_id, {field}) VALUES(?, 1)
            ON CONFLICT(user_id) DO UPDATE SET {field}={field}+1""",
            (user_id,),
        )
        cur = conn.execute(
            "SELECT memes, videos, tournaments FROM progress WHERE user_id=?",
            (user_id,),
        )
        row = cur.fetchone()
        counts = {
            "memes": row[0],
            "videos": row[1],
            "tournaments": row[2],
        }
        new_achs: list[str] = []
        for data in ACHIEVEMENTS.values():
            if counts[data["field"]] >= data["threshold"]:
                if _add_achievement(conn, user_id, data["name"], data["emoji"]):
                    new_achs.append(f"{data['emoji']} {data['name']}")
        conn.commit()
        return new_achs


def record_meme(user_id: int) -> list[str]:
    """Increase meme counter and return newly earned achievements."""
    return _increment(user_id, "memes")


def record_video(user_id: int) -> list[str]:
    """Increase video counter and return newly earned achievements."""
    return _increment(user_id, "videos")


def record_tournament(user_id: int) -> list[str]:
    """Increase tournament counter and return newly earned achievements."""
    return _increment(user_id, "tournaments")


def get_user_achievements(user_id: int) -> list[str]:
    """Return list of achievements for a user."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "SELECT achievement FROM user_achievements WHERE user_id=?",
            (user_id,),
        )
        return [row[0] for row in cur.fetchall()]
