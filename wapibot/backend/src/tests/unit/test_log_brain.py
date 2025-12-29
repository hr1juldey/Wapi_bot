"""Unit tests for log node brain integration."""

import pytest
from unittest.mock import patch, MagicMock
from nodes.atomic import log
from workflows.shared.state import BookingState


@pytest.mark.asyncio
async def test_log_saves_to_brain_when_enabled():
    """Test log saves events to brain_gym.db when brain is enabled."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "I want to book a service",
        "history": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"}
        ],
        "current_step": "extraction",
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "shadow"
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

        result = await log.node(
            state,
            event_type="extraction_success",
            event_data={"field": "customer.first_name", "confidence": 0.95},
            severity="info"
        )

        # Verify state unchanged (logging is side-effect only)
        assert result == state

        # Verify brain repository called
        assert mock_repo.save.called
        saved_decision = mock_repo.save.call_args[0][0]
        assert saved_decision.decision_id.startswith("log_")
        assert saved_decision.conversation_id == "test_12345"
        assert saved_decision.brain_mode == "shadow"
        assert saved_decision.action_taken == "log:extraction_success"
        assert saved_decision.workflow_outcome == "info"


@pytest.mark.asyncio
async def test_log_skips_brain_when_disabled():
    """Test log skips brain when brain_enabled=False."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = False
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

        result = await log.node(
            state,
            event_type="test_event",
            event_data={"test": "data"},
            severity="info"
        )

        # Brain repository NOT called
        assert not mock_repo.save.called


@pytest.mark.asyncio
async def test_log_skips_brain_when_rl_gym_disabled():
    """Test log skips brain when rl_gym_enabled=False."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.rl_gym_enabled = False

    mock_repo = MagicMock()

    with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

        result = await log.node(
            state,
            event_type="test_event",
            event_data={"test": "data"},
            severity="info"
        )

        # Brain repository NOT called
        assert not mock_repo.save.called


@pytest.mark.asyncio
async def test_log_handles_brain_save_error():
    """Test log continues workflow even if brain save fails."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "shadow"
    mock_settings.rl_gym_enabled = True

    # Mock repository that raises error
    mock_repo = MagicMock()
    mock_repo.save.side_effect = Exception("Database write failed")

    with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

        # Should NOT raise exception
        result = await log.node(
            state,
            event_type="test_event",
            event_data={"test": "data"},
            severity="error"
        )

        # Workflow continues normally
        assert result == state


@pytest.mark.asyncio
async def test_log_serializes_event_data():
    """Test log properly serializes event data in state snapshot."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [
            {"role": "user", "content": "Message 1"}
        ],
        "current_step": "api_call",
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "conscious"
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    event_data = {
        "endpoint": "get_available_slots",
        "latency_ms": 234,
        "status": "success",
        "slot_count": 5
    }

    with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

        await log.node(
            state,
            event_type="api_call",
            event_data=event_data,
            severity="info"
        )

        # Verify saved decision
        assert mock_repo.save.called
        saved_decision = mock_repo.save.call_args[0][0]

        # Verify state snapshot contains event data
        import json
        state_snapshot = json.loads(saved_decision.state_snapshot)
        assert state_snapshot["event_type"] == "api_call"
        assert state_snapshot["severity"] == "info"
        assert state_snapshot["data"]["endpoint"] == "get_available_slots"
        assert state_snapshot["data"]["latency_ms"] == 234
        assert state_snapshot["data"]["status"] == "success"


@pytest.mark.asyncio
async def test_log_handles_none_event_data():
    """Test log handles None event_data gracefully."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "shadow"
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

        await log.node(
            state,
            event_type="simple_event",
            event_data=None,  # No data
            severity="debug"
        )

        # Verify saved decision
        saved_decision = mock_repo.save.call_args[0][0]

        import json
        state_snapshot = json.loads(saved_decision.state_snapshot)
        assert state_snapshot["data"] == {}  # Empty dict for None


@pytest.mark.asyncio
async def test_log_limits_conversation_history():
    """Test log only saves last 3 messages."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [
            {"role": "user", "content": f"Message {i}"}
            for i in range(10)  # 10 messages
        ],
        "current_step": "test",
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "shadow"
    mock_settings.rl_gym_enabled = True

    mock_repo = MagicMock()

    with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
         patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

        await log.node(
            state,
            event_type="test_event",
            event_data={"test": "data"},
            severity="info"
        )

        # Verify only last 3 messages saved
        saved_decision = mock_repo.save.call_args[0][0]
        import json
        conv_history = json.loads(saved_decision.conversation_history)
        assert len(conv_history) == 3
        assert conv_history[0]["content"] == "Message 7"  # Last 3 messages
        assert conv_history[-1]["content"] == "Message 9"


@pytest.mark.asyncio
async def test_log_severity_levels():
    """Test log handles different severity levels correctly."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "response": "",
        "should_proceed": True
    }

    mock_settings = MagicMock()
    mock_settings.brain_enabled = True
    mock_settings.brain_mode = "shadow"
    mock_settings.rl_gym_enabled = True

    severities = ["debug", "info", "warning", "error"]

    for severity in severities:
        mock_repo = MagicMock()

        with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
             patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

            await log.node(
                state,
                event_type=f"test_{severity}",
                event_data={"severity_test": True},
                severity=severity
            )

            # Verify workflow_outcome matches severity
            saved_decision = mock_repo.save.call_args[0][0]
            assert saved_decision.workflow_outcome == severity


@pytest.mark.asyncio
async def test_log_different_brain_modes():
    """Test log records brain_mode correctly."""
    state: BookingState = {
        "conversation_id": "test_12345",
        "user_message": "Test",
        "history": [],
        "current_step": "test",
        "response": "",
        "should_proceed": True
    }

    brain_modes = ["shadow", "reflex", "conscious"]

    for mode in brain_modes:
        mock_settings = MagicMock()
        mock_settings.brain_enabled = True
        mock_settings.brain_mode = mode
        mock_settings.rl_gym_enabled = True

        mock_repo = MagicMock()

        with patch('nodes.atomic.log.get_brain_settings', return_value=mock_settings), \
             patch('nodes.atomic.log.BrainDecisionRepository', return_value=mock_repo):

            await log.node(
                state,
                event_type="mode_test",
                event_data={"mode": mode},
                severity="info"
            )

            # Verify brain_mode recorded correctly
            saved_decision = mock_repo.save.call_args[0][0]
            assert saved_decision.brain_mode == mode
