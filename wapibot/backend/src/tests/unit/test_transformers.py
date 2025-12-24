"""Unit tests for transformers."""

import pytest
from transformers.filter_services import FilterServicesByVehicle
from transformers.format_slot_options import FormatSlotOptions


def test_filter_services_by_vehicle_type():
    """Test FilterServicesByVehicle filters correctly."""
    services = [
        {"product_name": "Car Wash", "vehicle_type": "Hatchback", "base_price": 299},
        {"product_name": "SUV Wash", "vehicle_type": "SUV", "base_price": 499},
        {"product_name": "Basic Wash", "vehicle_type": "Hatchback", "base_price": 199},
        {"product_name": "Sedan Wash", "vehicle_type": "Sedan", "base_price": 349}
    ]

    state = {"vehicle": {"vehicle_type": "Hatchback"}}

    transformer = FilterServicesByVehicle()
    result = transformer(services, state)

    assert len(result) == 2
    assert all(s["vehicle_type"] == "Hatchback" for s in result)
    assert result[0]["product_name"] == "Car Wash"
    assert result[1]["product_name"] == "Basic Wash"


def test_filter_services_case_insensitive():
    """Test FilterServicesByVehicle is case insensitive."""
    services = [
        {"product_name": "Service 1", "vehicle_type": "hatchback", "base_price": 100},
        {"product_name": "Service 2", "vehicle_type": "HATCHBACK", "base_price": 200}
    ]

    state = {"vehicle": {"vehicle_type": "Hatchback"}}

    transformer = FilterServicesByVehicle()
    result = transformer(services, state)

    assert len(result) == 2


def test_filter_services_no_vehicle_type():
    """Test FilterServicesByVehicle returns all when no vehicle type."""
    services = [
        {"product_name": "Service 1", "vehicle_type": "Hatchback", "base_price": 100},
        {"product_name": "Service 2", "vehicle_type": "SUV", "base_price": 200}
    ]

    state = {}  # No vehicle type

    transformer = FilterServicesByVehicle()
    result = transformer(services, state)

    assert len(result) == 2  # Returns all services


def test_filter_services_no_matches():
    """Test FilterServicesByVehicle with no matching services."""
    services = [
        {"product_name": "SUV Wash", "vehicle_type": "SUV", "base_price": 499}
    ]

    state = {"vehicle": {"vehicle_type": "Hatchback"}}

    transformer = FilterServicesByVehicle()
    result = transformer(services, state)

    assert len(result) == 0


def test_format_slot_options_with_slots():
    """Test FormatSlotOptions formats slots correctly."""
    slots = [
        {"date": "2025-12-25", "time_slot": "10:00 AM - 12:00 PM", "available": True},
        {"date": "2025-12-25", "time_slot": "2:00 PM - 4:00 PM", "available": True},
        {"date": "2025-12-26", "time_slot": "10:00 AM - 12:00 PM", "available": True}
    ]

    state = {}

    transformer = FormatSlotOptions()
    result = transformer(slots, state)

    assert "Available Appointment Slots" in result
    assert "2025-12-25" in result
    assert "2025-12-26" in result
    assert "10:00 AM - 12:00 PM" in result
    assert "2:00 PM - 4:00 PM" in result


def test_format_slot_options_filters_unavailable():
    """Test FormatSlotOptions filters out unavailable slots."""
    slots = [
        {"date": "2025-12-25", "time_slot": "10:00 AM - 12:00 PM", "available": True},
        {"date": "2025-12-25", "time_slot": "2:00 PM - 4:00 PM", "available": False}
    ]

    state = {}

    transformer = FormatSlotOptions()
    result = transformer(slots, state)

    assert "10:00 AM - 12:00 PM" in result
    assert "2:00 PM - 4:00 PM" not in result


def test_format_slot_options_no_slots():
    """Test FormatSlotOptions with no slots."""
    slots = []

    state = {}

    transformer = FormatSlotOptions()
    result = transformer(slots, state)

    assert "no appointment slots are available" in result.lower()


def test_format_slot_options_all_unavailable():
    """Test FormatSlotOptions with all slots unavailable."""
    slots = [
        {"date": "2025-12-25", "time_slot": "10:00 AM - 12:00 PM", "available": False},
        {"date": "2025-12-25", "time_slot": "2:00 PM - 4:00 PM", "available": False}
    ]

    state = {}

    transformer = FormatSlotOptions()
    result = transformer(slots, state)

    assert "no appointment slots are available" in result.lower()


def test_format_slot_options_groups_by_date():
    """Test FormatSlotOptions groups slots by date."""
    slots = [
        {"date": "2025-12-25", "time_slot": "10:00 AM", "available": True},
        {"date": "2025-12-26", "time_slot": "11:00 AM", "available": True},
        {"date": "2025-12-25", "time_slot": "2:00 PM", "available": True}
    ]

    state = {}

    transformer = FormatSlotOptions()
    result = transformer(slots, state)

    # Should have 2025-12-25 with 2 slots before 2025-12-26
    date_25_pos = result.find("2025-12-25")
    date_26_pos = result.find("2025-12-26")

    assert date_25_pos < date_26_pos
