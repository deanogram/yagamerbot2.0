import sqlite3
import time
from pathlib import Path

LOG_DB_PATH = Path(__file__).resolve().parent.parent / "moderation_log.db"


def init_modlog_db() -> None:
    """Initialize database for moderation logs and strikes."""
    with sqlite3.connect(LOG_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                moderator_id INTEGER,
                action TEXT,
                reason TEXT,
                timestamp INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS strikes(
                user_id INTEGER PRIMARY KEY,
                count INTEGER DEFAULT 0,
                last_timestamp INTEGER
            )
            """
        )
        conn.commit()


def log_action(user_id: int, moderator_id: int, action: str, reason: str = "") -> None:
    """Log moderation action."""
    with sqlite3.connect(LOG_DB_PATH) as conn:
        conn.execute(
            "INSERT INTO logs(user_id, moderator_id, action, reason, timestamp) VALUES(?,?,?,?,?)",
            (user_id, moderator_id, action, reason, int(time.time())),
        )
        conn.commit()


def add_strike(user_id: int) -> int:
    """Increase strike count for a user and return new count."""
    ts = int(time.time())
    with sqlite3.connect(LOG_DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO strikes(user_id, count, last_timestamp) VALUES(?, 1, ?)
            ON CONFLICT(user_id) DO UPDATE SET count=count+1, last_timestamp=excluded.last_timestamp
            RETURNING count
            """,
            (user_id, ts),
        )
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else 1


def get_strikes(user_id: int) -> int:
    with sqlite3.connect(LOG_DB_PATH) as conn:
        cur = conn.execute("SELECT count FROM strikes WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else 0


def clear_strikes(user_id: int) -> None:
    with sqlite3.connect(LOG_DB_PATH) as conn:
        conn.execute("DELETE FROM strikes WHERE user_id=?", (user_id,))
        conn.commit()
