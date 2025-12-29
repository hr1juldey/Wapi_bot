"""Unit tests for workflow nodes."""

import pytest
from workflows.existing_user_booking import (
    extract_service_selection_node,
    extract_slot_selection_node,
    extract_confirmation_node
)


@pytest.mark.asyncio
async def test_extract_service_selection_with_number():
    """Test service selection extraction with number."""
    state = {
        "user_message": "I want service 2",
        "filtered_services": [
            {"product_name": "Basic Wash", "base_price": 299},
            {"product_name": "Premium Wash", "base_price": 499},
            {"product_name": "Deluxe Wash", "base_price": 699}
        ]
    }

    result = await extract_service_selection_node(state)

    assert result["service_selected"] is True
    assert result["selected_service"]["product_name"] == "Premium Wash"
    assert result["selected_service"]["base_price"] == 499


@pytest.mark.asyncio
async def test_extract_service_selection_with_name():
    """Test service selection extraction with service name."""
    state = {
        "user_message": "I want the premium wash please",
        "filtered_services": [
            {"product_name": "Basic Wash", "base_price": 299},
            {"product_name": "Premium Wash", "base_price": 499}
        ]
    }

    result = await extract_service_selection_node(state)

    assert result["service_selected"] is True
    assert result["selected_service"]["product_name"] == "Premium Wash"


@pytest.mark.asyncio
async def test_extract_service_selection_invalid_number():
    """Test service selection extraction with invalid number."""
    state = {
        "user_message": "I want service 10",
        "filtered_services": [
            {"product_name": "Basic Wash", "base_price": 299}
        ]
    }

    result = await extract_service_selection_node(state)

    assert result["service_selected"] is False
    assert "selection_error" in result


@pytest.mark.asyncio
async def test_extract_service_selection_unclear():
    """Test service selection extraction with unclear message."""
    state = {
        "user_message": "What is the price?",
        "filtered_services": [
            {"product_name": "Basic Wash", "base_price": 299}
        ]
    }

    result = await extract_service_selection_node(state)

    assert result["service_selected"] is False
    assert "selection_error" in result


@pytest.mark.asyncio
async def test_extract_slot_selection_with_date():
    """Test slot selection extraction with date mention."""
    state = {
        "user_message": "I want 2025-12-26 morning slot",
        "available_slots": [
            {"date": "2025-12-26", "time_slot": "10:00 AM - 12:00 PM", "slot_id": "SLOT-001", "available": True},
            {"date": "2025-12-27", "time_slot": "10:00 AM - 12:00 PM", "slot_id": "SLOT-002", "available": True}
        ]
    }

    result = await extract_slot_selection_node(state)

    assert result["slot_selected"] is True
    assert result["appointment"]["date"] == "2025-12-26"
    assert result["appointment"]["slot_id"] == "SLOT-001"


@pytest.mark.asyncio
async def test_extract_slot_selection_with_time():
    """Test slot selection extraction with time mention."""
    state = {
        "user_message": "I want the 2:00 PM - 4:00 PM slot",  # Exact match
        "available_slots": [
            {"date": "2025-12-26", "time_slot": "10:00 AM - 12:00 PM", "slot_id": "SLOT-001", "available": True},
            {"date": "2025-12-26", "time_slot": "2:00 PM - 4:00 PM", "slot_id": "SLOT-002", "available": True}
        ]
    }

    result = await extract_slot_selection_node(state)

    assert result["slot_selected"] is True
    assert result["appointment"]["time_slot"] == "2:00 PM - 4:00 PM"


@pytest.mark.asyncio
async def test_extract_slot_selection_skip_unavailable():
    """Test slot selection skips unavailable slots."""
    state = {
        "user_message": "2025-12-27",
        "available_slots": [
            {"date": "2025-12-27", "time_slot": "10:00 AM - 12:00 PM", "slot_id": "SLOT-001", "available": False},
            {"date": "2025-12-27", "time_slot": "2:00 PM - 4:00 PM", "slot_id": "SLOT-002", "available": True}
        ]
    }

    result = await extract_slot_selection_node(state)

    # Should select the available slot for the same date
    assert result["slot_selected"] is True
    assert result["appointment"]["slot_id"] == "SLOT-002"


@pytest.mark.asyncio
async def test_extract_confirmation_yes():
    """Test confirmation extraction with YES."""
    state = {"user_message": "Yes, please confirm"}

    result = await extract_confirmation_node(state)

    assert result["confirmed"] is True


@pytest.mark.asyncio
async def test_extract_confirmation_no():
    """Test confirmation extraction with NO."""
    state = {"user_message": "No, cancel it"}

    result = await extract_confirmation_node(state)

    assert result["confirmed"] is False


@pytest.mark.asyncio
async def test_extract_confirmation_unclear():
    """Test confirmation extraction with unclear response."""
    state = {"user_message": "Maybe later"}

    result = await extract_confirmation_node(state)

    assert result["confirmed"] is None


# Note: Routing functions (check_*) are tested implicitly through extraction tests
# and workflow integration tests. They're simple conditional logic that doesn't
# need separate unit tests.
