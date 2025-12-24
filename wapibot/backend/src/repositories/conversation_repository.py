"""Repository for conversation state persistence.

Handles CRUD operations for conversation states and history.
Uses async SQLite for storage.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from workflows.shared.state import BookingState
from db.connection import db_connection

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation state and history."""

    async def save_state(
        self,
        conversation_id: str,
        booking_state: BookingState,
        state: str,
        completeness: float
    ) -> int:
        """Save versioned conversation state.

        Args:
            conversation_id: Unique conversation ID
            booking_state: Current BookingState
            state: State name (collecting, confirmation, completed)
            completeness: Completeness percentage (0-100)

        Returns:
            Version number

        Example:
            >>> await repo.save_state("919876543210", state, "collecting", 60.0)
            1
        """
        conn = await db_connection.connect()

        # Get current version
        cursor = await conn.execute(
            "SELECT MAX(version) FROM conversation_states WHERE conversation_id = ?",
            (conversation_id,)
        )
        row = await cursor.fetchone()
        version = (row[0] or 0) + 1

        # Save new version
        await conn.execute(
            """
            INSERT INTO conversation_states
            (conversation_id, version, state, booking_state_json, completeness)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, version, state, json.dumps(booking_state), completeness)
        )

        await conn.commit()
        logger.info(f"Saved state v{version} for {conversation_id}")
        return version

    async def get_state(
        self,
        conversation_id: str
    ) -> Optional[BookingState]:
        """Get latest conversation state.

        Args:
            conversation_id: Unique conversation ID

        Returns:
            Latest BookingState or None

        Example:
            >>> state = await repo.get_state("919876543210")
        """
        conn = await db_connection.connect()

        cursor = await conn.execute(
            """
            SELECT booking_state_json
            FROM conversation_states
            WHERE conversation_id = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (conversation_id,)
        )

        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])

        return None

    async def get_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, str]]:
        """Get conversation history.

        Args:
            conversation_id: Unique conversation ID
            limit: Maximum turns to return

        Returns:
            List of {role, content} dicts

        Example:
            >>> history = await repo.get_history("919876543210")
        """
        conn = await db_connection.connect()

        cursor = await conn.execute(
            """
            SELECT role, content
            FROM conversation_history
            WHERE conversation_id = ?
            ORDER BY turn_number ASC
            LIMIT ?
            """,
            (conversation_id, limit)
        )

        rows = await cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in rows]

    async def add_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        turn_number: int,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add conversation turn to history.

        Args:
            conversation_id: Unique conversation ID
            role: "user" or "assistant"
            content: Message content
            turn_number: Turn sequence number
            extracted_data: Optional extracted data

        Example:
            >>> await repo.add_turn("919876543210", "user", "Hi", 1)
        """
        conn = await db_connection.connect()

        extracted_json = json.dumps(extracted_data) if extracted_data else None

        await conn.execute(
            """
            INSERT INTO conversation_history
            (conversation_id, turn_number, role, content, extracted_data_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, turn_number, role, content, extracted_json)
        )

        await conn.commit()
        logger.debug(f"Added turn {turn_number} for {conversation_id}")
