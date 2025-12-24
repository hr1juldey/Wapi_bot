"""Unit tests for send_message atomic node."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from nodes.atomic import send_message
from workflows.shared.state import BookingState


@pytest.mark.asyncio
async def test_send_message_with_static_builder():
    """Test send_message with simple static message builder."""
    state = {
        "conversation_id": "919876543210",
        "history": []
    }

    # Simple MessageBuilder
    def static_builder(s):
        return "Hello from Yawlit!"

    # Mock WAPI client and call_api
    with patch('nodes.atomic.send_message.get_wapi_client') as mock_client, \
         patch('nodes.atomic.send_message.call_api_node', new_callable=AsyncMock) as mock_call_api:

        # Configure mocks
        mock_wapi = MagicMock()
        mock_wapi.base_url = "https://wapi.in.net"
        mock_wapi.vendor_uid = "test_vendor"
        mock_wapi.bearer_token = "test_token"
        mock_wapi.from_phone_number_id = "test_phone_id"
        mock_client.return_value = mock_wapi

        # Mock call_api to return success
        async def mock_api_call(state, builder, path, retry_count, on_failure):
            state["wapi_response"] = {"status": "sent"}
            return state

        mock_call_api.side_effect = mock_api_call

        # Call node
        result = await send_message.node(state, static_builder)

        # Assertions
        assert "wapi_response" in result
        assert len(result["history"]) == 1
        assert result["history"][0]["role"] == "assistant"
        assert result["history"][0]["content"] == "Hello from Yawlit!"
        assert mock_call_api.called


@pytest.mark.asyncio
async def test_send_message_with_dynamic_builder():
    """Test send_message with state-dependent dynamic builder."""
    state = {
        "conversation_id": "919876543210",
        "customer": {"first_name": "Rahul", "last_name": "Sharma"},
        "history": []
    }

    # Dynamic MessageBuilder using state
    def dynamic_builder(s):
        first_name = s.get("customer", {}).get("first_name", "there")
        return f"Hello {first_name}! Welcome to Yawlit."

    with patch('nodes.atomic.send_message.get_wapi_client') as mock_client, \
         patch('nodes.atomic.send_message.call_api_node', new_callable=AsyncMock) as mock_call_api:

        # Configure mocks
        mock_wapi = MagicMock()
        mock_wapi.base_url = "https://wapi.in.net"
        mock_wapi.vendor_uid = "test_vendor"
        mock_wapi.bearer_token = "test_token"
        mock_wapi.from_phone_number_id = "test_phone_id"
        mock_client.return_value = mock_wapi

        async def mock_api_call(state, builder, path, retry_count, on_failure):
            state["wapi_response"] = {"status": "sent"}
            return state

        mock_call_api.side_effect = mock_api_call

        result = await send_message.node(state, dynamic_builder)

        assert "Hello Rahul!" in result["history"][-1]["content"]


@pytest.mark.asyncio
async def test_send_message_builder_error():
    """Test error handling when message builder fails."""
    state = {
        "conversation_id": "919876543210",
        "history": []
    }

    # Failing MessageBuilder
    def failing_builder(s):
        raise ValueError("Builder failed intentionally")

    result = await send_message.node(state, failing_builder, on_failure="log")

    # Should log error and return state
    assert "message_builder_error" in result.get("errors", [])
    assert "wapi_response" not in result


@pytest.mark.asyncio
async def test_send_message_no_phone_number():
    """Test error handling when conversation_id is missing."""
    state = {
        # No conversation_id
        "history": []
    }

    def simple_builder(s):
        return "Test message"

    result = await send_message.node(state, simple_builder)

    # Should log error and return
    assert "no_phone_number" in result.get("errors", [])
    assert "wapi_response" not in result


@pytest.mark.asyncio
async def test_send_message_no_history_storage():
    """Test that history storage can be disabled."""
    state = {
        "conversation_id": "919876543210",
        "history": []
    }

    def simple_builder(s):
        return "Test message"

    with patch('nodes.atomic.send_message.get_wapi_client') as mock_client, \
         patch('nodes.atomic.send_message.call_api_node', new_callable=AsyncMock) as mock_call_api:

        mock_wapi = MagicMock()
        mock_wapi.base_url = "https://wapi.in.net"
        mock_wapi.vendor_uid = "test_vendor"
        mock_wapi.bearer_token = "test_token"
        mock_wapi.from_phone_number_id = "test_phone_id"
        mock_client.return_value = mock_wapi

        async def mock_api_call(state, builder, path, retry_count, on_failure):
            state["wapi_response"] = {"status": "sent"}
            return state

        mock_call_api.side_effect = mock_api_call

        result = await send_message.node(state, simple_builder, store_in_history=False)

        # History should not be updated
        assert len(result.get("history", [])) == 0
