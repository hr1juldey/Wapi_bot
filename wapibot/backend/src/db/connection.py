"""SQLite database connection management.

Provides async SQLite connection using aiosqlite.
Single database file for all conversation state.
"""

import aiosqlite
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = Path(__file__).parent.parent.parent / "data" / "conversations.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class DatabaseConnection:
    """Async SQLite database connection manager."""

    _instance: Optional['DatabaseConnection'] = None
    _db: Optional[aiosqlite.Connection] = None

    def __new__(cls):
        """Singleton pattern - one connection pool."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> aiosqlite.Connection:
        """Get database connection.

        Returns:
            Async SQLite connection

        Example:
            >>> db = DatabaseConnection()
            >>> conn = await db.connect()
        """
        if self._db is None:
            self._db = await aiosqlite.connect(str(DB_PATH))
            self._db.row_factory = aiosqlite.Row
            logger.info(f"Database connected: {DB_PATH}")

        return self._db

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("Database connection closed")

    async def init_tables(self) -> None:
        """Initialize database tables.

        Creates tables if they don't exist.
        """
        conn = await self.connect()

        # Conversation states table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_states (
                conversation_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                state TEXT NOT NULL,
                booking_state_json TEXT NOT NULL,
                completeness REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (conversation_id, version)
            )
        """)

        # Conversation history table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                turn_number INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                extracted_data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conv_id
            ON conversation_states(conversation_id)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_conv_id
            ON conversation_history(conversation_id)
        """)

        await conn.commit()
        logger.info("Database tables initialized")


# Global instance
db_connection = DatabaseConnection()
