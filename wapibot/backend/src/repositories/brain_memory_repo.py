"""Brain memory repository - CRUD for memory bank."""

import sqlite3
from typing import List, Optional, Dict, Any
from core.brain_config import get_brain_settings


class BrainMemoryRepository:
    """Repository for brain memory records."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize repository with database path."""
        if db_path is None:
            settings = get_brain_settings()
            db_path = settings.rl_gym_db_path
        self.db_path = db_path

    def save(self, memory: Dict[str, Any]) -> None:
        """Save memory to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO brain_memories VALUES (?, ?, ?, ?, ?, ?)
        """, (
            memory.get("memory_id"),
            memory.get("conversation_id"),
            memory.get("timestamp"),
            memory.get("user_message"),
            memory.get("conversation_quality", 0.5),
            memory.get("user_satisfaction")
        ))

        conn.commit()
        conn.close()

    def get_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent memories for dream processing."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM brain_memories
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
