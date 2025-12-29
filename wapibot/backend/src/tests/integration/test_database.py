"""Integration tests for database layer.

Tests SQLModel connection, tables, and repository operations.
"""

import pytest
import json
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.db_models import ConversationStateTable, ConversationHistoryTable
from repositories.conversation_repository import ConversationRepository


class TestDatabaseTables:
    """Test SQLModel table creation and basic operations."""

    @pytest.mark.asyncio
    async def test_create_conversation_state(self, test_db_session: AsyncSession):
        """Test creating a conversation state record."""
        state = ConversationStateTable(
            conversation_id="test_conv_001",
            version=1,
            state="collecting",
            booking_state_json='{"name": "Test"}',
            completeness=0.5,
        )

        test_db_session.add(state)
        await test_db_session.commit()

        # Verify it was created
        result = await test_db_session.execute(
            select(ConversationStateTable)
            .where(ConversationStateTable.conversation_id == "test_conv_001")
        )
        retrieved = result.scalar_one()

        assert retrieved.conversation_id == "test_conv_001"
        assert retrieved.version == 1
        assert retrieved.state == "collecting"
        assert retrieved.completeness == 0.5

    @pytest.mark.asyncio
    async def test_conversation_state_versioning(self, test_db_session: AsyncSession):
        """Test versioned state storage."""
        conv_id = "test_conv_002"

        # Create multiple versions
        for version in [1, 2, 3]:
            state = ConversationStateTable(
                conversation_id=conv_id,
                version=version,
                state="collecting",
                booking_state_json=f'{{"version": {version}}}',
                completeness=version * 0.3,
            )
            test_db_session.add(state)

        await test_db_session.commit()

        # Retrieve all versions
        result = await test_db_session.execute(
            select(ConversationStateTable)
            .where(ConversationStateTable.conversation_id == conv_id)
            .order_by(ConversationStateTable.version)
        )
        versions = result.scalars().all()

        assert len(versions) == 3
        assert versions[0].version == 1
        assert versions[2].version == 3

    @pytest.mark.asyncio
    async def test_create_conversation_history(self, test_db_session: AsyncSession):
        """Test creating conversation history records."""
        turn = ConversationHistoryTable(
            conversation_id="test_conv_003",
            turn_number=1,
            role="user",
            content="Hello, I need a car wash",
            extracted_data_json='{"intent": "booking"}',
        )

        test_db_session.add(turn)
        await test_db_session.commit()

        # Verify it was created
        result = await test_db_session.execute(
            select(ConversationHistoryTable)
            .where(ConversationHistoryTable.conversation_id == "test_conv_003")
        )
        retrieved = result.scalar_one()

        assert retrieved.conversation_id == "test_conv_003"
        assert retrieved.turn_number == 1
        assert retrieved.role == "user"
        assert "car wash" in retrieved.content

    @pytest.mark.asyncio
    async def test_conversation_history_ordering(self, test_db_session: AsyncSession):
        """Test conversation history turn ordering."""
        conv_id = "test_conv_004"

        # Add turns in random order
        for turn_num in [3, 1, 2]:
            turn = ConversationHistoryTable(
                conversation_id=conv_id,
                turn_number=turn_num,
                role="user" if turn_num % 2 else "assistant",
                content=f"Turn {turn_num}",
            )
            test_db_session.add(turn)

        await test_db_session.commit()

        # Retrieve in order
        result = await test_db_session.execute(
            select(ConversationHistoryTable)
            .where(ConversationHistoryTable.conversation_id == conv_id)
            .order_by(ConversationHistoryTable.turn_number)
        )
        turns = result.scalars().all()

        assert len(turns) == 3
        assert turns[0].turn_number == 1
        assert turns[1].turn_number == 2
        assert turns[2].turn_number == 3


class TestConversationRepository:
    """Test ConversationRepository with SQLModel."""

    @pytest.mark.asyncio
    async def test_save_state(self, test_db_session: AsyncSession, monkeypatch):
        """Test saving conversation state via repository."""
        # Mock db_connection to use test session
        from repositories import conversation_repository

        async def mock_get_session():
            return test_db_session

        # Create mock db_connection
        class MockDBConnection:
            async def get_session(self):
                return test_db_session

        monkeypatch.setattr(
            conversation_repository,
            "db_connection",
            MockDBConnection()
        )

        repo = ConversationRepository()
        booking_state = {
            "name": {"first": "Ravi", "last": "Kumar"},
            "phone": "+919876543210"
        }

        version = await repo.save_state(
            conversation_id="test_conv_005",
            booking_state=booking_state,
            state="collecting",
            completeness=0.6
        )

        assert version == 1

        # Verify in database
        result = await test_db_session.execute(
            select(ConversationStateTable)
            .where(ConversationStateTable.conversation_id == "test_conv_005")
        )
        state = result.scalar_one()

        assert state.version == 1
        assert state.state == "collecting"
        assert state.completeness == 0.6

    @pytest.mark.asyncio
    async def test_get_state(self, test_db_session: AsyncSession, monkeypatch):
        """Test retrieving latest conversation state."""
        # Add test data
        conv_id = "test_conv_006"
        booking_data = {"name": "Test User"}

        state = ConversationStateTable(
            conversation_id=conv_id,
            version=2,
            state="confirmation",
            booking_state_json=json.dumps(booking_data),
            completeness=0.9
        )
        test_db_session.add(state)
        await test_db_session.commit()

        # Mock db_connection
        from repositories import conversation_repository

        class MockDBConnection:
            async def get_session(self):
                return test_db_session

        monkeypatch.setattr(
            conversation_repository,
            "db_connection",
            MockDBConnection()
        )

        repo = ConversationRepository()
        result = await repo.get_state(conv_id)

        assert result is not None
        assert result["conversation_id"] == conv_id
        assert result["version"] == 2
        assert result["state"] == "confirmation"
        assert result["completeness"] == 0.9
        assert result["booking_state"]["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_get_state_none_if_not_exists(self, test_db_session: AsyncSession, monkeypatch):
        """Test that get_state returns None for non-existent conversation."""
        from repositories import conversation_repository

        class MockDBConnection:
            async def get_session(self):
                return test_db_session

        monkeypatch.setattr(
            conversation_repository,
            "db_connection",
            MockDBConnection()
        )

        repo = ConversationRepository()
        result = await repo.get_state("nonexistent_conv")

        assert result is None

    @pytest.mark.asyncio
    async def test_add_turn(self, test_db_session: AsyncSession, monkeypatch):
        """Test adding conversation turn via repository."""
        from repositories import conversation_repository

        class MockDBConnection:
            async def get_session(self):
                return test_db_session

        monkeypatch.setattr(
            conversation_repository,
            "db_connection",
            MockDBConnection()
        )

        repo = ConversationRepository()
        extracted_data = {"intent": "greeting"}

        await repo.add_turn(
            conversation_id="test_conv_007",
            turn_number=1,
            role="user",
            content="Hello there",
            extracted_data=extracted_data
        )

        # Verify in database
        result = await test_db_session.execute(
            select(ConversationHistoryTable)
            .where(ConversationHistoryTable.conversation_id == "test_conv_007")
        )
        turn = result.scalar_one()

        assert turn.turn_number == 1
        assert turn.role == "user"
        assert turn.content == "Hello there"
        assert json.loads(turn.extracted_data_json) == extracted_data

    @pytest.mark.asyncio
    async def test_get_history(self, test_db_session: AsyncSession, monkeypatch):
        """Test retrieving conversation history."""
        conv_id = "test_conv_008"

        # Add test turns
        turns_data = [
            (1, "user", "Hi"),
            (2, "assistant", "Hello!"),
            (3, "user", "I need help"),
        ]

        for turn_num, role, content in turns_data:
            turn = ConversationHistoryTable(
                conversation_id=conv_id,
                turn_number=turn_num,
                role=role,
                content=content
            )
            test_db_session.add(turn)

        await test_db_session.commit()

        # Mock and retrieve
        from repositories import conversation_repository

        class MockDBConnection:
            async def get_session(self):
                return test_db_session

        monkeypatch.setattr(
            conversation_repository,
            "db_connection",
            MockDBConnection()
        )

        repo = ConversationRepository()
        history = await repo.get_history(conv_id)

        assert len(history) == 3
        assert history[0]["turn_number"] == 1
        assert history[0]["role"] == "user"
        assert history[1]["content"] == "Hello!"
        assert history[2]["turn_number"] == 3
