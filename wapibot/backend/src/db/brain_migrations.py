"""Brain database migrations."""

import sqlite3
from db.brain_tables import (
    BRAIN_DECISIONS_TABLE,
    BRAIN_MEMORIES_TABLE,
    BRAIN_DREAMS_TABLE
)


def create_brain_tables(db_path: str) -> None:
    """Create all brain tables in SQLite database.

    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute(BRAIN_DECISIONS_TABLE)
    cursor.execute(BRAIN_MEMORIES_TABLE)
    cursor.execute(BRAIN_DREAMS_TABLE)

    conn.commit()
    conn.close()


def init_brain_db() -> None:
    """Initialize brain database with default path."""
    from core.brain_config import get_brain_settings

    settings = get_brain_settings()
    create_brain_tables(settings.rl_gym_db_path)
