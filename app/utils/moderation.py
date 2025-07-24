import sqlite3
from pathlib import Path

MOD_DB_PATH = Path(__file__).resolve().parent.parent / "moderation.db"


def init_moderation_db() -> None:
    """Create tables for banned words and links."""
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
