"""Unit tests for message builders."""

from message_builders.greeting import GreetingBuilder
from message_builders.service_catalog import ServiceCatalogBuilder
from message_builders.booking_confirmation import BookingConfirmationBuilder


def test_greeting_builder_with_customer_name():
    """Test GreetingBuilder with customer first name."""
    state = {
        "customer": {"first_name": "Rahul", "last_name": "Sharma"}
    }

    builder = GreetingBuilder()
    message = builder(state)

    assert "Hi Rahul" in message
    assert "Welcome back to Yawlit" in message
    assert "👋" in message


def test_greeting_builder_without_customer_name():
    """Test GreetingBuilder without customer name."""
    state = {}

    builder = GreetingBuilder()
    message = builder(state)

    assert "Hello!" in message
    assert "Welcome back to Yawlit" in message
    assert "👋" in message


def test_service_catalog_builder_with_services():
    """Test ServiceCatalogBuilder with multiple services."""
    state = {
        "filtered_services": [
            {"product_name": "Premium Wash", "base_price": 499, "description": "Complete wash and wax"},
            {"product_name": "Basic Wash", "base_price": 299, "description": "Quick exterior wash"}
        ]
    }

    builder = ServiceCatalogBuilder()
    message = builder(state)

    assert "Premium Wash" in message
    assert "₹499" in message
    assert "Basic Wash" in message
    assert "₹299" in message
    assert "1." in message  # Numbered list
    assert "2." in message


def test_service_catalog_builder_with_no_services():
    """Test ServiceCatalogBuilder with no services."""
    state = {"filtered_services": []}

    builder = ServiceCatalogBuilder()
    message = builder(state)

    assert "no services are available" in message.lower()


def test_service_catalog_builder_with_long_description():
    """Test ServiceCatalogBuilder truncates long descriptions."""
    long_desc = "A" * 100  # 100 character description
    state = {
        "filtered_services": [
            {"product_name": "Service", "base_price": 100, "description": long_desc}
        ]
    }

    builder = ServiceCatalogBuilder()
    message = builder(state)

    # Should truncate to 80 chars + "..."
    assert "..." in message


def test_booking_confirmation_builder_complete():
    """Test BookingConfirmationBuilder with all details."""
    state = {
        "customer": {"first_name": "Rahul"},
        "vehicle": {"brand": "TATA", "model": "Nexon", "number_plate": "MH12AB1234"},
        "selected_service": {"product_name": "Premium Wash", "base_price": 499},
        "appointment": {"date": "2025-12-25", "time_slot": "10:00 AM - 12:00 PM"},
        "total_price": 499
    }

    builder = BookingConfirmationBuilder()
    message = builder(state)

    assert "Booking Confirmation" in message
    assert "Rahul" in message
    assert "TATA Nexon" in message
    assert "MH12AB1234" in message
    assert "Premium Wash" in message
    assert "2025-12-25" in message
    assert "10:00 AM - 12:00 PM" in message
    assert "₹499" in message
    assert "YES" in message
    assert "NO" in message


def test_booking_confirmation_builder_minimal():
    """Test BookingConfirmationBuilder with minimal data."""
    state = {
        "selected_service": {"product_name": "Basic Wash"},
        "total_price": 299
    }

    builder = BookingConfirmationBuilder()
    message = builder(state)

    assert "Booking Confirmation" in message
    assert "Basic Wash" in message
    assert "₹299" in message
    assert "YES" in message


def test_booking_confirmation_builder_no_price():
    """Test BookingConfirmationBuilder with missing price."""
    state = {
        "selected_service": {"product_name": "Service"}
    }

    builder = BookingConfirmationBuilder()
    message = builder(state)

    assert "Booking Confirmation" in message
    assert "₹0" in message  # Default price
