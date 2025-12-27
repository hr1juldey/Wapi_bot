"""SQLite connection management for WebSocket session audit logs.

Provides async SQLite connection for websocket_sessions.db.
Separate database from conversations.db for clear separation of concerns.
"""

from pathlib import Path
from typing import Optional
import logging
import os
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.websocket_session import WebSocketSessionTable

logger = logging.getLogger(__name__)

# Explicitly reference table to avoid "unused import" warnings
__all__ = ['WebSocketDatabaseConnection', 'websocket_db_connection', 'WebSocketSessionTable']

# Database configuration
WEBSOCKET_DB_PATH = Path(__file__).parent.parent.parent / "data" / "websocket_sessions.db"
WEBSOCKET_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Security: Set restrictive permissions on database directory
try:
    os.chmod(WEBSOCKET_DB_PATH.parent, 0o700)  # Only owner can read/write/execute
    logger.debug(f"WebSocket DB directory permissions set to 0o700: {WEBSOCKET_DB_PATH.parent}")
except Exception as e:
    logger.warning(f"Could not set WebSocket DB directory permissions: {e}")

# SQLite async connection string
WEBSOCKET_DATABASE_URL = f"sqlite+aiosqlite:///{WEBSOCKET_DB_PATH}"


class WebSocketDatabaseConnection:
    """Async SQLite database connection manager for WebSocket sessions."""

    _instance: Optional['WebSocketDatabaseConnection'] = None
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
            Async SQLAlchemy engine for websocket_sessions.db
        """
        if self._engine is None:
            self._engine = create_async_engine(
                WEBSOCKET_DATABASE_URL,
                echo=False,  # Set True for SQL query logging
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,  # For SQLite
            )
            logger.info(f"WebSocket database engine created: {WEBSOCKET_DB_PATH}")

        return self._engine

    async def get_session(self) -> AsyncSession:
        """Get async database session.

        Returns:
            Async SQLAlchemy session for queries

        Example:
            >>> db = websocket_db_connection
            >>> async with await db.get_session() as session:
            ...     result = await session.execute(select(WebSocketSessionTable))
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
        """Initialize WebSocket session tables.

        Creates websocket_sessions table if it doesn't exist.
        """
        engine = await self.get_engine()

        # Create all tables for WebSocket sessions
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Security: Set restrictive permissions on database file
        if WEBSOCKET_DB_PATH.exists():
            try:
                os.chmod(WEBSOCKET_DB_PATH, 0o600)  # Only owner can read/write
                logger.debug(f"WebSocket DB file permissions set to 0o600: {WEBSOCKET_DB_PATH}")
            except Exception as e:
                logger.warning(f"Could not set WebSocket DB file permissions: {e}")

        logger.info("WebSocket session tables initialized")

    async def close(self) -> None:
        """Close database connection and dispose engine."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("WebSocket database connection closed")


# Global instance
websocket_db_connection = WebSocketDatabaseConnection()
