import sqlite3
import time
from pathlib import Path
from .modlog import log_action, add_strike

MOD_DB_PATH = Path(__file__).resolve().parent.parent / "moderation.db"


def init_moderation_db() -> None:
    """Create tables for moderation data."""
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS banned_words(
                word TEXT PRIMARY KEY
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS banned_links(
                link TEXT PRIMARY KEY
            )
            """
        )
        cur = conn.execute("SELECT COUNT(*) FROM banned_words")
        if cur.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO banned_words(word) VALUES(?)",
                [
                    ("spam",),
                    ("junk",),
                    ("badword",),
                    ("хуй",),
                    ("пизда",),
                    ("блять",),
                    ("сука",),
                ],
            )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS warnings(
                user_id INTEGER PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mutes(
                user_id INTEGER PRIMARY KEY,
                until INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bans(
                user_id INTEGER PRIMARY KEY,
                until INTEGER DEFAULT 0
            )
            """
        )
        # ensure column 'until' exists for older databases
        try:
            conn.execute("ALTER TABLE bans ADD COLUMN until INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admins(
                user_id INTEGER PRIMARY KEY
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS moderators(
                user_id INTEGER PRIMARY KEY
            )
            """
        )
        conn.commit()


def get_banned_words() -> set[str]:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute("SELECT word FROM banned_words")
        return {row[0].lower() for row in cur.fetchall()}


def get_banned_links() -> set[str]:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute("SELECT link FROM banned_links")
        return {row[0].lower() for row in cur.fetchall()}


def add_banned_word(word: str) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO banned_words(word) VALUES(?)",
            (word.lower(),),
        )
        conn.commit()


def add_banned_link(link: str) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO banned_links(link) VALUES(?)",
            (link.lower(),),
        )
        conn.commit()


def add_warning(user_id: int, moderator_id: int = 0, reason: str = "") -> int:
    """Increase warning count, log and return new count."""
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO warnings(user_id, count) VALUES(?, 1)
            ON CONFLICT(user_id) DO UPDATE SET count=count+1
            RETURNING count
            """,
            (user_id,),
        )
        count = cur.fetchone()[0]
        conn.commit()
    log_action(user_id, moderator_id, "warn", reason)
    add_strike(user_id)
    return count


def get_warnings(user_id: int) -> int:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute(
            "SELECT count FROM warnings WHERE user_id=?",
            (user_id,),
        )
        row = cur.fetchone()
        return row[0] if row else 0


def clear_warnings(user_id: int) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute(
            "DELETE FROM warnings WHERE user_id=?",
            (user_id,),
        )
        conn.commit()


def mute_user(user_id: int, seconds: int, moderator_id: int = 0, reason: str = "") -> int:
    """Mute user for given seconds. 0 means permanent mute."""
    until = 0 if seconds <= 0 else int(time.time() + seconds)
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO mutes(user_id, until) VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET until=excluded.until
            """,
            (user_id, until),
        )
        conn.commit()
    log_action(user_id, moderator_id, "mute", reason)
    return until


def unmute_user(user_id: int) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute("DELETE FROM mutes WHERE user_id=?", (user_id,))
        conn.commit()


def is_muted(user_id: int) -> bool:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute("SELECT until FROM mutes WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return False
        if row[0] == 0:
            return True
        if row[0] > int(time.time()):
            return True
        conn.execute("DELETE FROM mutes WHERE user_id=?", (user_id,))
        conn.commit()
        return False


def ban_user(user_id: int, seconds: int = 0, moderator_id: int = 0, reason: str = "") -> int:
    """Ban user for given seconds. 0 means permanent ban."""
    until = 0 if seconds <= 0 else int(time.time() + seconds)
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute(
            "INSERT INTO bans(user_id, until) VALUES(?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET until=excluded.until",
            (user_id, until),
        )
        conn.commit()
    log_action(user_id, moderator_id, "ban", reason)
    return until


def unban_user(user_id: int) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
        conn.commit()


def is_banned(user_id: int) -> bool:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute("SELECT until FROM bans WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return False
        if row[0] == 0:
            return True
        if row[0] > int(time.time()):
            return True
        conn.execute("DELETE FROM bans WHERE user_id=?", (user_id,))
        conn.commit()
        return False


def get_all_mutes() -> list[tuple[int, int]]:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute("SELECT user_id, until FROM mutes")
        return cur.fetchall()


def get_all_bans() -> list[tuple[int, int]]:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute("SELECT user_id, until FROM bans")
        return cur.fetchall()


def add_admin(user_id: int) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO admins(user_id) VALUES(?)",
            (user_id,),
        )
        conn.commit()


def remove_admin(user_id: int) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        conn.commit()


def get_admins() -> list[int]:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute("SELECT user_id FROM admins")
        return [row[0] for row in cur.fetchall()]


def add_moderator(user_id: int) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO moderators(user_id) VALUES(?)",
            (user_id,),
        )
        conn.commit()


def remove_moderator(user_id: int) -> None:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        conn.execute("DELETE FROM moderators WHERE user_id=?", (user_id,))
        conn.commit()


def get_moderators() -> list[int]:
    with sqlite3.connect(MOD_DB_PATH) as conn:
        cur = conn.execute("SELECT user_id FROM moderators")
        return [row[0] for row in cur.fetchall()]
