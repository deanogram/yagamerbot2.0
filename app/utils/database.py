import sqlite3
from pathlib import Path
from aiogram.types import User

DB_PATH = Path(__file__).resolve().parent.parent / "users.db"


def init_db() -> None:
    """Initialize the database and create tables if needed."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                xp INTEGER DEFAULT 0,
                sent_total INTEGER DEFAULT 0,
                sent_approved INTEGER DEFAULT 0,
                sent_rejected INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()


def add_user(user: User) -> None:
    """Insert or update user basic information."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO users(user_id, name, username)
            VALUES(?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                username=excluded.username
            """,
            (user.id, user.full_name, user.username or ""),
        )
        conn.commit()


def increment_submission(user_id: int) -> None:
    """Increase total submissions count."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET sent_total = sent_total + 1 WHERE user_id=?",
            (user_id,),
        )
        conn.commit()


def record_result(user_id: int, approved: bool) -> None:
    """Record moderation result and award XP if approved."""
    with sqlite3.connect(DB_PATH) as conn:
        if approved:
            conn.execute(
                """
                UPDATE users
                SET sent_approved = sent_approved + 1,
                    xp = xp + 2
                WHERE user_id=?
                """,
                (user_id,),
            )
        else:
            conn.execute(
                "UPDATE users SET sent_rejected = sent_rejected + 1 WHERE user_id=?",
                (user_id,),
            )
        conn.commit()


def add_xp(user_id: int, amount: int) -> None:
    """Increase user's XP by the given amount."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET xp = xp + ? WHERE user_id=?",
            (amount, user_id),
        )
        conn.commit()


def get_user_stats(user_id: int) -> dict | None:
    """Return statistics for a user."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_user_ids() -> list[int]:
    """Return list of all user IDs."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT user_id FROM users")
        return [row[0] for row in cur.fetchall()]

TOURNAMENT_DB_PATH = Path(__file__).resolve().parent.parent / "tournaments.db"


def init_tournament_db() -> None:
    """Create table for tournament ratings if it doesn't exist."""
    with sqlite3.connect(TOURNAMENT_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ratings (
                user_id INTEGER PRIMARY KEY,
                score INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()


def get_tournament_ratings(limit: int = 10) -> list[tuple]:
    """Return top players with their scores."""
    with sqlite3.connect(TOURNAMENT_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT user_id, score FROM ratings ORDER BY score DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()

    results = []
    for idx, row in enumerate(rows, 1):
        user = get_user_stats(row["user_id"])
        name = user.get("name") if user else f"User {row['user_id']}"
        results.append((idx, name, row["score"]))
    return results


TOURNAMENT_INFO_DB_PATH = Path(__file__).resolve().parent.parent / "tournaments_info.db"


def init_tournament_info_db() -> None:
    """Create table for tournament info."""
    with sqlite3.connect(TOURNAMENT_INFO_DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game TEXT,
                type TEXT,
                date TEXT,
                prize TEXT,
                preview TEXT
            )
            """
        )
        # try to add missing column "prize" for older versions
        try:
            conn.execute("ALTER TABLE tournaments ADD COLUMN prize TEXT")
        except sqlite3.OperationalError:
            pass
        # try to add missing column "preview" for older versions
        try:
            conn.execute("ALTER TABLE tournaments ADD COLUMN preview TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()


def add_tournament(game: str, type_: str, date: str, prize: str, preview: str | None) -> None:
    with sqlite3.connect(TOURNAMENT_INFO_DB_PATH) as conn:
        conn.execute(
            "INSERT INTO tournaments(game, type, date, prize, preview) VALUES(?,?,?,?,?)",
            (game, type_, date, prize, preview),
        )
        conn.commit()


def get_tournaments() -> list[tuple]:
    with sqlite3.connect(TOURNAMENT_INFO_DB_PATH) as conn:
        cur = conn.execute(
            "SELECT id, game, type, date, prize, preview FROM tournaments ORDER BY id DESC"
        )
        return cur.fetchall()


def update_tournament(
    tid: int, game: str, type_: str, date: str, prize: str, preview: str | None
) -> None:
    """Update tournament information by id."""
    with sqlite3.connect(TOURNAMENT_INFO_DB_PATH) as conn:
        conn.execute(
            """
            UPDATE tournaments
            SET game=?, type=?, date=?, prize=?, preview=?
            WHERE id=?
            """,
            (game, type_, date, prize, preview, tid),
        )
        conn.commit()


def delete_tournament(tid: int) -> None:
    """Remove tournament from the database."""
    with sqlite3.connect(TOURNAMENT_INFO_DB_PATH) as conn:
        conn.execute("DELETE FROM tournaments WHERE id=?", (tid,))
        conn.commit()
