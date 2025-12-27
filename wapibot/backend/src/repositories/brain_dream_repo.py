"""Brain dream repository - CRUD for dream learnings."""

import sqlite3
from typing import List, Optional
from models.dream_config import DreamResult
from core.brain_config import get_brain_settings


class BrainDreamRepository:
    """Repository for dream cycle results."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize repository."""
        if db_path is None:
            settings = get_brain_settings()
            db_path = settings.rl_gym_db_path
        self.db_path = db_path

    def save(self, dream: DreamResult) -> None:
        """Save dream result to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO brain_dreams VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            dream.dream_id, dream.timestamp, dream.model_used,
            dream.conversations_processed, dream.dreams_generated,
            dream.patterns_learned, ""  # dream_data placeholder
        ))

        conn.commit()
        conn.close()

    def get_recent(self, limit: int = 10) -> List[DreamResult]:
        """Get recent dream cycles."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM brain_dreams ORDER BY timestamp DESC LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [DreamResult(**dict(row)) for row in rows]
