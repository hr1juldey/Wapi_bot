"""Integration tests for brain observation system.

Tests checkpoint and log nodes writing to actual brain_gym.db database.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from nodes.atomic import checkpoint, log
from workflows.shared.state import BookingState
from repositories.brain_decision_repo import BrainDecisionRepository
from db.brain_migrations import create_brain_tables


class TestBrainObservationIntegration:
    """Integration tests for brain observation with real database."""

    @pytest.fixture
    def temp_brain_db(self):
        """Create temporary brain database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        # Create tables
        create_brain_tables(db_path)

        yield db_path

        # Cleanup
        os.unlink(db_path)

    @pytest.fixture
    def test_state(self) -> BookingState:
        """Create test booking state."""
        return {
            "conversation_id": "integration_test_12345",
            "user_message": "I want to book a car wash",
            "history": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello! How can I help?"},
                {"role": "user", "content": "I want to book a car wash"}
            ],
            "current_step": "customer_info",
            "completeness": 0.3,
            "errors": [],
            "response": "",
            "should_proceed": True,
            "customer": {"first_name": "Riju", "phone": "1234567890"},
            "vehicle": None,
            "selected_service": None,
            "slot": None
        }

    @pytest.mark.asyncio
    async def test_checkpoint_writes_to_database(self, temp_brain_db, test_state):
        """Test checkpoint writes milestone to real database."""
        # Override brain settings to use temp DB
        from unittest.mock import patch
        from core.brain_config import BrainSettings

        mock_settings = BrainSettings(
            brain_enabled=True,
            brain_mode="shadow",
            rl_gym_enabled=True,
            rl_gym_db_path=temp_brain_db
        )

        with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings):
            # Call checkpoint node
            result = await checkpoint.node(
                test_state,
                checkpoint_name="customer_confirmed",
                checkpoint_type="milestone",
                save_to_brain=True
            )

        # Verify state updated
        assert "checkpoints" in result
        assert len(result["checkpoints"]) == 1

        # Verify database record
        repo = BrainDecisionRepository(temp_brain_db)
        decisions = repo.get_recent(limit=10)

        assert len(decisions) == 1
        decision = decisions[0]
        assert decision.decision_id.startswith("chk_")
        assert decision.conversation_id == "integration_test_12345"
        assert decision.action_taken == "checkpoint:customer_confirmed"
        assert decision.workflow_outcome == "milestone"
        assert decision.brain_mode == "shadow"

        # Verify serialized data
        state_snapshot = json.loads(decision.state_snapshot)
        assert state_snapshot["completeness"] == 0.3
        assert state_snapshot["current_step"] == "customer_info"

        conv_history = json.loads(decision.conversation_history)
        assert len(conv_history) == 3

    @pytest.mark.asyncio
    async def test_log_writes_to_database(self, temp_brain_db, test_state):
        """Test log writes event to real database."""
        from unittest.mock import patch
        from core.brain_config import BrainSettings

        mock_settings = BrainSettings(
            brain_enabled=True,
            brain_mode="shadow",
            rl_gym_enabled=True,
            rl_gym_db_path=temp_brain_db
        )

        event_data = {
            "field": "customer.first_name",
            "method": "dspy",
            "confidence": 0.95
        }

        with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings):
            # Call log node
            result = await log.node(
                test_state,
                event_type="extraction_success",
                event_data=event_data,
                severity="info"
            )

        # Verify state unchanged (logging is side-effect)
        assert result == test_state

        # Verify database record
        repo = BrainDecisionRepository(temp_brain_db)
        decisions = repo.get_recent(limit=10)

        assert len(decisions) == 1
        decision = decisions[0]
        assert decision.decision_id.startswith("log_")
        assert decision.conversation_id == "integration_test_12345"
        assert decision.action_taken == "log:extraction_success"
        assert decision.workflow_outcome == "info"
        assert decision.brain_mode == "shadow"

        # Verify event data
        state_snapshot = json.loads(decision.state_snapshot)
        assert state_snapshot["event_type"] == "extraction_success"
        assert state_snapshot["severity"] == "info"
        assert state_snapshot["data"]["field"] == "customer.first_name"
        assert state_snapshot["data"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_multiple_checkpoints_and_logs(self, temp_brain_db, test_state):
        """Test multiple checkpoints and logs create separate records."""
        from unittest.mock import patch
        from core.brain_config import BrainSettings

        mock_settings = BrainSettings(
            brain_enabled=True,
            brain_mode="reflex",
            rl_gym_enabled=True,
            rl_gym_db_path=temp_brain_db
        )

        with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
             patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings):

            # Create multiple observations
            result = await checkpoint.node(
                test_state,
                checkpoint_name="customer_confirmed",
                checkpoint_type="milestone",
                save_to_brain=True
            )

            result = await log.node(
                result,
                event_type="extraction_success",
                event_data={"field": "customer.name"},
                severity="info"
            )

            result = await checkpoint.node(
                result,
                checkpoint_name="slot_selected",
                checkpoint_type="milestone",
                save_to_brain=True
            )

            result = await log.node(
                result,
                event_type="api_call",
                event_data={"endpoint": "get_slots", "latency_ms": 150},
                severity="info"
            )

        # Verify all 4 records in database
        repo = BrainDecisionRepository(temp_brain_db)
        decisions = repo.get_recent(limit=10)

        assert len(decisions) == 4

        # Verify records in reverse chronological order
        assert decisions[0].action_taken == "log:api_call"
        assert decisions[1].action_taken == "checkpoint:slot_selected"
        assert decisions[2].action_taken == "log:extraction_success"
        assert decisions[3].action_taken == "checkpoint:customer_confirmed"

        # Verify all have same conversation_id
        for decision in decisions:
            assert decision.conversation_id == "integration_test_12345"
            assert decision.brain_mode == "reflex"

    @pytest.mark.asyncio
    async def test_brain_observation_workflow_resilience(self, temp_brain_db, test_state):
        """Test workflow continues even if brain database unavailable."""
        from unittest.mock import patch
        from core.brain_config import BrainSettings

        # Use non-existent directory for DB path
        invalid_db_path = "/nonexistent/path/brain_gym.db"

        mock_settings = BrainSettings(
            brain_enabled=True,
            brain_mode="shadow",
            rl_gym_enabled=True,
            rl_gym_db_path=invalid_db_path
        )

        with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
             patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings):

            # Checkpoint should not crash
            result = await checkpoint.node(
                test_state,
                checkpoint_name="test",
                checkpoint_type="milestone",
                save_to_brain=True
            )

            # State should still be updated
            assert "checkpoints" in result
            assert len(result["checkpoints"]) == 1

            # Log should not crash
            result = await log.node(
                result,
                event_type="test",
                event_data={"test": "data"},
                severity="info"
            )

            # State should be unchanged
            assert result is not None

    @pytest.mark.asyncio
    async def test_brain_modes_recorded_correctly(self, temp_brain_db, test_state):
        """Test different brain modes are recorded correctly."""
        from unittest.mock import patch
        from core.brain_config import BrainSettings

        modes = ["shadow", "reflex", "conscious"]

        for mode in modes:
            mock_settings = BrainSettings(
                brain_enabled=True,
                brain_mode=mode,
                rl_gym_enabled=True,
                rl_gym_db_path=temp_brain_db
            )

            with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings):
                await checkpoint.node(
                    test_state,
                    checkpoint_name=f"{mode}_checkpoint",
                    checkpoint_type="milestone",
                    save_to_brain=True
                )

        # Verify all 3 modes recorded
        repo = BrainDecisionRepository(temp_brain_db)
        decisions = repo.get_recent(limit=10)

        assert len(decisions) == 3

        recorded_modes = {d.brain_mode for d in decisions}
        assert recorded_modes == {"shadow", "reflex", "conscious"}

    @pytest.mark.asyncio
    async def test_conversation_history_trimming(self, temp_brain_db, test_state):
        """Test conversation history is trimmed to last N messages."""
        from unittest.mock import patch
        from core.brain_config import BrainSettings

        # Add many messages to history
        test_state["history"] = [
            {"role": "user", "content": f"Message {i}"}
            for i in range(20)
        ]

        mock_settings = BrainSettings(
            brain_enabled=True,
            brain_mode="shadow",
            rl_gym_enabled=True,
            rl_gym_db_path=temp_brain_db
        )

        with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
             patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings):

            # Checkpoint saves last 5 messages
            await checkpoint.node(
                test_state,
                checkpoint_name="test_checkpoint",
                checkpoint_type="milestone",
                save_to_brain=True
            )

            # Log saves last 3 messages
            await log.node(
                test_state,
                event_type="test_event",
                event_data={},
                severity="info"
            )

        repo = BrainDecisionRepository(temp_brain_db)
        decisions = repo.get_recent(limit=10)

        # Verify checkpoint has 5 messages
        checkpoint_decision = [d for d in decisions if d.action_taken.startswith("checkpoint")][0]
        checkpoint_history = json.loads(checkpoint_decision.conversation_history)
        assert len(checkpoint_history) == 5

        # Verify log has 3 messages
        log_decision = [d for d in decisions if d.action_taken.startswith("log")][0]
        log_history = json.loads(log_decision.conversation_history)
        assert len(log_history) == 3
