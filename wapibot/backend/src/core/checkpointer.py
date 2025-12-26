"""LangGraph checkpointer manager with in-memory primary and SQLite backup.

This module provides a dual-layer checkpointing system:
- Primary: MemorySaver (fast, in-memory)
- Backup: AsyncSqliteSaver (persistent, SQLite DB)

The checkpointers are initialized at FastAPI startup and properly
cleaned up at shutdown.
"""

import logging
from pathlib import Path
from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

logger = logging.getLogger(__name__)


class CheckpointerManager:
    """Manages LangGraph checkpointers with proper lifecycle.

    Provides both in-memory (primary) and SQLite (backup) checkpointers.
    """

    def __init__(self):
        self._memory_checkpointer: Optional[MemorySaver] = None
        self._sqlite_checkpointer: Optional[AsyncSqliteSaver] = None
        self._sqlite_context = None

    async def initialize(self, db_path: Optional[Path] = None):
        """Initialize both checkpointers at application startup.

        Args:
            db_path: Path to SQLite database file. Defaults to backend/data/langgraph_checkpoints.db
        """
        logger.info("🔧 Initializing checkpointers...")

        # Initialize in-memory checkpointer (primary)
        self._memory_checkpointer = MemorySaver()
        logger.info("✅ MemorySaver initialized (primary)")

        # Initialize SQLite checkpointer (backup)
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "langgraph_checkpoints.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Use async context manager properly
        self._sqlite_context = AsyncSqliteSaver.from_conn_string(str(db_path))
        self._sqlite_checkpointer = await self._sqlite_context.__aenter__()

        logger.info(f"✅ AsyncSqliteSaver initialized (backup) at {db_path}")

    async def shutdown(self):
        """Cleanup checkpointers at application shutdown."""
        logger.info("🛑 Shutting down checkpointers...")

        if self._sqlite_context is not None:
            try:
                await self._sqlite_context.__aexit__(None, None, None)
                logger.info("✅ AsyncSqliteSaver closed")
            except Exception as e:
                logger.error(f"❌ Error closing AsyncSqliteSaver: {e}")

        # MemorySaver doesn't need explicit cleanup
        self._memory_checkpointer = None
        logger.info("✅ MemorySaver cleared")

    @property
    def memory(self) -> MemorySaver:
        """Get the in-memory checkpointer (primary, fast)."""
        if self._memory_checkpointer is None:
            raise RuntimeError("Checkpointer not initialized. Call initialize() first.")
        return self._memory_checkpointer

    @property
    def sqlite(self) -> AsyncSqliteSaver:
        """Get the SQLite checkpointer (backup, persistent)."""
        if self._sqlite_checkpointer is None:
            raise RuntimeError("Checkpointer not initialized. Call initialize() first.")
        return self._sqlite_checkpointer


# Global checkpointer manager instance
checkpointer_manager = CheckpointerManager()