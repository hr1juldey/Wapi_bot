"""Repository for conversation state persistence using SQLModel.

Handles CRUD operations for conversation states and history.
Uses SQLModel ORM for type-safe database operations.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from sqlmodel import select, func

from workflows.shared.state import BookingState
from db.connection import db_connection
from db.db_models import ConversationStateTable, ConversationHistoryTable

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation state and history using SQLModel ORM."""

    async def save_state(
        self,
        conversation_id: str,
        booking_state: BookingState,
        state: str,
        completeness: float
    ) -> int:
        """Save versioned conversation state using SQLModel.

        Args:
            conversation_id: Unique conversation ID
            booking_state: Current BookingState
            state: State name (collecting, confirmation, completed)
            completeness: Completeness score (0-1)

        Returns:
            Version number

        Example:
            >>> await repo.save_state("conv_123", state, "collecting", 0.6)
            1
        """
        async with await db_connection.get_session() as session:
            # Get current max version using SQLModel query
            result = await session.execute(
                select(func.max(ConversationStateTable.version))
                .where(ConversationStateTable.conversation_id == conversation_id)
            )
            max_version = result.scalar()
            version = (max_version or 0) + 1

            # Create new state record
            new_state = ConversationStateTable(
                conversation_id=conversation_id,
                version=version,
                state=state,
                booking_state_json=json.dumps(booking_state),
                completeness=completeness
            )

            session.add(new_state)
            await session.commit()

            logger.info(f"Saved state v{version} for {conversation_id}")
            return version

    async def get_state(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest conversation state using SQLModel.

        Args:
            conversation_id: Unique conversation ID

        Returns:
            Dict with state, booking_state, completeness, version or None

        Example:
            >>> state = await repo.get_state("conv_123")
            >>> print(state["version"])
            1
        """
        async with await db_connection.get_session() as session:
            # Get latest version
            result = await session.execute(
                select(ConversationStateTable)
                .where(ConversationStateTable.conversation_id == conversation_id)
                .order_by(ConversationStateTable.version.desc())
                .limit(1)
            )
            state_record = result.scalar_one_or_none()

            if not state_record:
                return None

            return {
                "conversation_id": state_record.conversation_id,
                "version": state_record.version,
                "state": state_record.state,
                "booking_state": json.loads(state_record.booking_state_json),
                "completeness": state_record.completeness,
                "created_at": state_record.created_at
            }

    async def get_history(
        self,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history using SQLModel.

        Args:
            conversation_id: Unique conversation ID

        Returns:
            List of conversation turns

        Example:
            >>> history = await repo.get_history("conv_123")
            >>> len(history)
            5
        """
        async with await db_connection.get_session() as session:
            result = await session.execute(
                select(ConversationHistoryTable)
                .where(ConversationHistoryTable.conversation_id == conversation_id)
                .order_by(ConversationHistoryTable.turn_number)
            )
            records = result.scalars().all()

            return [
                {
                    "turn_number": record.turn_number,
                    "role": record.role,
                    "content": record.content,
                    "extracted_data": json.loads(record.extracted_data_json) if record.extracted_data_json else None,
                    "created_at": record.created_at
                }
                for record in records
            ]

    async def add_turn(
        self,
        conversation_id: str,
        turn_number: int,
        role: str,
        content: str,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add conversation turn using SQLModel.

        Args:
            conversation_id: Unique conversation ID
            turn_number: Turn number
            role: "user" or "assistant"
            content: Message content
            extracted_data: Optional extracted data dict

        Example:
            >>> await repo.add_turn("conv_123", 1, "user", "Hello", {"intent": "greeting"})
        """
        async with await db_connection.get_session() as session:
            new_turn = ConversationHistoryTable(
                conversation_id=conversation_id,
                turn_number=turn_number,
                role=role,
                content=content,
                extracted_data_json=json.dumps(extracted_data) if extracted_data else None
            )

            session.add(new_turn)
            await session.commit()

            logger.info(f"Added turn {turn_number} for {conversation_id}")