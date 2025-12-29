"""Unit tests for checkpoint node brain integration."""

import pytest
from unittest.mock import patch, MagicMock
from nodes.atomic import checkpoint
from workflows.shared.state import BookingState


@pytest.mark.asyncio
async def test_checkpoint_saves_to_brain_when_enabled():
    """Test checkpoint saves to brain_gym.db when brain is enabled."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "I want to book a car wash",
        "history": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"}
        ],
        "current_step": "customer_info",
        "completeness": 0.5,
        "errors": [],
        "response": "",
        "should_proceed": True
    }

    # Mock brain settings (enabled)
    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "shadow"
    mock_settings.rl_gym_enabled = True

    # Mock repository
    mock_repo = MagicMock()

    with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.checkpoint.BrainDecisionRepository', return_value=mock_repo):

        result = await checkpoint.node(
            state,
            checkpoint_name="customer_confirmed",
            checkpoint_type="milestone",
            save_to_brain=True
        )

        # Verify checkpoint added to state
        assert "checkpoints" in result
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["name"] == "customer_confirmed"
        assert result["checkpoints"][0]["type"] == "milestone"

        # Verify brain repository called
        assert mock_repo.save.called
        saved_decision = mock_repo.save.call_args[0][0]
        assert saved_decision.decision_id.startswith("chk_")
        assert saved_decision.conversation_id == "test_12345"
        assert saved_decision.brain_mode == "shadow"
        assert saved_decision.action_taken == "checkpoint:customer_confirmed"
        assert saved_decision.workflow_outcome == "milestone"


@pytest.mark.asyncio
async def test_checkpoint_skips_brain_when_disabled():
    """Test checkpoint skips brain when brain_enabled=False."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "completeness": 0.0,
        "errors": [],
        "response": "",
        "should_proceed": True
    }

    # Mock brain settings (disabled)
    mock_settings = MagicMock()
    mock_settings.brain_enabled = False
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.checkpoint.BrainDecisionRepository', return_value=mock_repo):

        result = await checkpoint.node(
            state,
            checkpoint_name="test_checkpoint",
            checkpoint_type="milestone",
            save_to_brain=True
        )

        # Checkpoint still added to state
        assert "checkpoints" in result
        assert len(result["checkpoints"]) == 1

        # Brain repository NOT called
        assert not mock_repo.save.called


@pytest.mark.asyncio
async def test_checkpoint_skips_brain_when_rl_gym_disabled():
    """Test checkpoint skips brain when rl_gym_enabled=False."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "completeness": 0.0,
        "errors": [],
        "response": "",
        "should_proceed": True
    }

    # Mock brain settings (brain enabled but RL Gym disabled)
    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.rl_gym_enabled = False

    mock_repo = MagicMock()

    with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.checkpoint.BrainDecisionRepository', return_value=mock_repo):

        result = await checkpoint.node(
            state,
            checkpoint_name="test_checkpoint",
            checkpoint_type="milestone",
            save_to_brain=True
        )

        # Checkpoint added to state
        assert "checkpoints" in result

        # Brain repository NOT called
        assert not mock_repo.save.called


@pytest.mark.asyncio
async def test_checkpoint_skips_brain_when_save_to_brain_false():
    """Test checkpoint skips brain when save_to_brain=False."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "completeness": 0.0,
        "errors": [],
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.checkpoint.BrainDecisionRepository', return_value=mock_repo):

        result = await checkpoint.node(
            state,
            checkpoint_name="test_checkpoint",
            checkpoint_type="milestone",
            save_to_brain=False  # Explicitly disabled
        )

        # Checkpoint added to state
        assert "checkpoints" in result

        # Brain repository NOT called
        assert not mock_repo.save.called


@pytest.mark.asyncio
async def test_checkpoint_handles_brain_save_error():
    """Test checkpoint continues workflow even if brain save fails."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "completeness": 0.0,
        "errors": [],
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "shadow"
    mock_settings.rl_gym_enabled = True

    # Mock repository that raises error
    mock_repo = MagicMock()
    mock_repo.save.side_effect = Exception("Database connection failed")

    with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.checkpoint.BrainDecisionRepository', return_value=mock_repo):

        # Should NOT raise exception
        result = await checkpoint.node(
            state,
            checkpoint_name="test_checkpoint",
            checkpoint_type="milestone",
            save_to_brain=True
        )

        # Workflow continues normally
        assert "checkpoints" in result
        assert len(result["checkpoints"]) == 1


@pytest.mark.asyncio
async def test_checkpoint_serializes_state_snapshot():
    """Test checkpoint properly serializes state snapshot."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Reply 1"}
        ],
        "current_step": "slot_selection",
        "completeness": 0.75,
        "errors": ["validation_error"],
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "reflex"
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.checkpoint.BrainDecisionRepository', return_value=mock_repo):

        result = await checkpoint.node(
            state,
            checkpoint_name="slot_selected",
            checkpoint_type="decision_point",
            save_to_brain=True
        )

        # Verify saved decision
        assert mock_repo.save.called
        saved_decision = mock_repo.save.call_args[0][0]

        # Verify state snapshot is JSON serializable
        import json
        state_snapshot = json.loads(saved_decision.state_snapshot)
        assert state_snapshot["completeness"] == 0.75
        assert state_snapshot["current_step"] == "slot_selection"
        assert "validation_error" in state_snapshot["errors"]

        # Verify conversation history is JSON serializable
        conv_history = json.loads(saved_decision.conversation_history)
        assert len(conv_history) == 2


@pytest.mark.asyncio
async def test_checkpoint_limits_conversation_history():
    """Test checkpoint only saves last 5 messages."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)  # 10 messages
        ],
        "current_step": "test",
        "completeness": 0.0,
        "errors": [],
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "shadow"
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    with patch('nodes.atomic.checkpoint.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.checkpoint.BrainDecisionRepository', return_value=mock_repo):

        await checkpoint.node(
            state,
            checkpoint_name="test",
            checkpoint_type="milestone",
            save_to_brain=True
        )

        # Verify only last 5 messages saved
        saved_decision = mock_repo.save.call_args[0][0]
        import json
        conv_history = json.loads(saved_decision.conversation_history)
        assert len(conv_history) == 5
        assert conv_history[0]["content"] == "Message 5"  # Last 5 messages
        assert conv_history[-1]["content"] == "Message 9"
