"""SQLModel database connection management.

Provides async SQLite connection using SQLModel engine.
Single database file for all conversation state.
"""

from pathlib import Path
from typing import Optional
import logging
import os
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import table models to register them with SQLModel metadata
from db.db_models import ConversationStateTable, ConversationHistoryTable

logger = logging.getLogger(__name__)

# Explicitly reference tables to avoid "unused import" warnings
__all__ = ['DatabaseConnection', 'db_connection', 'ConversationStateTable', 'ConversationHistoryTable']

# Database configuration
DB_PATH = Path(__file__).parent.parent.parent / "data" / "conversations.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Security: Set restrictive permissions on database directory
try:
    os.chmod(DB_PATH.parent, 0o700)  # Only owner can read/write/execute
    logger.debug(f"Database directory permissions set to 0o700: {DB_PATH.parent}")
except Exception as e:
    logger.warning(f"Could not set database directory permissions: {e}")

# SQLite async connection string
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"


class DatabaseConnection:
    """Async SQLite database connection manager using SQLModel."""

    _instance: Optional['DatabaseConnection'] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[sessionmaker] = None

    def __new__(cls):
        """Singleton pattern - one connection pool."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_engine(self) -> AsyncEngine:
        """Get async database engine.

        Returns:
            Async SQLAlchemy engine

        Example:
            >>> db = DatabaseConnection()
            >>> engine = await db.get_engine()
        """
        if self._engine is None:
            self._engine = create_async_engine(
                DATABASE_URL,
                echo=False,  # Set True for SQL query logging
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,  # For SQLite
            )
            logger.info(f"Database engine created: {DB_PATH}")

        return self._engine

    async def get_session(self) -> AsyncSession:
        """Get async database session.

        Returns:
            Async SQLAlchemy session for queries

        Example:
            >>> db = DatabaseConnection()
            >>> async with await db.get_session() as session:
            ...     result = await session.execute(select(ConversationStateTable))
        """
        if self._session_factory is None:
            engine = await self.get_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

        return self._session_factory()

    async def init_tables(self) -> None:
        """Initialize database tables using SQLModel.

        Creates all tables defined in db_models.py if they don't exist.
        """
        engine = await self.get_engine()

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Security: Set restrictive permissions on database file
        if DB_PATH.exists():
            try:
                os.chmod(DB_PATH, 0o600)  # Only owner can read/write
                logger.debug(f"Database file permissions set to 0o600: {DB_PATH}")
            except Exception as e:
                logger.warning(f"Could not set database file permissions: {e}")

        logger.info("Database tables initialized")

    async def close(self) -> None:
        """Close database connection and dispose engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connection closed")


# Global instance
db_connection = DatabaseConnection()
