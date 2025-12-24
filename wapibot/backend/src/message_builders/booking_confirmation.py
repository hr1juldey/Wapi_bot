"""Booking confirmation message builder.

SOLID Principles:
- Single Responsibility: ONLY builds booking confirmation messages
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements MessageBuilder Protocol
"""

from typing import Optional
from workflows.shared.state import BookingState


class BookingConfirmationBuilder:
    """Build booking confirmation messages with all details.

    Implements MessageBuilder Protocol for use with send_message.node().

    Usage:
        # Before creating the actual booking
        await send_message.node(state, BookingConfirmationBuilder())
    """

    def __call__(self, state: BookingState) -> str:
        """Build booking confirmation message from state.

        Args:
            state: Current booking state with customer, vehicle, service, appointment

        Returns:
            Formatted confirmation message

        Example:
            state = {
                "customer": {"first_name": "Rahul"},
                "vehicle": {"brand": "TATA", "model": "Nexon", "number_plate": "MH12AB1234"},
                "selected_service": {"product_name": "Premium Wash", "base_price": 499},
                "appointment": {"date": "2025-12-25", "time_slot": "10:00 AM - 12:00 PM"},
                "total_price": 499
            }
        """
        # Get booking details
        customer = state.get("customer", {})
        vehicle = state.get("vehicle", {})
        service = state.get("selected_service", {})
        appointment = state.get("appointment", {})
        total_price = state.get("total_price", 0)

        # Build confirmation message
        message = "📋 *Booking Confirmation*\n\n"

        # Customer details
        first_name = customer.get("first_name", "")
        if first_name:
            message += f"Customer: {first_name}\n"

        # Vehicle details
        brand = vehicle.get("brand", "")
        model = vehicle.get("model", "")
        number_plate = vehicle.get("number_plate", "")
        if brand and model:
            message += f"Vehicle: {brand} {model}"
            if number_plate:
                message += f" ({number_plate})"
            message += "\n"

        # Service details
        product_name = service.get("product_name", "Service")
        message += f"Service: {product_name}\n"

        # Appointment details
        date = appointment.get("date", "")
        time_slot = appointment.get("time_slot", "")
        if date:
            message += f"Date: {date}\n"
        if time_slot:
            message += f"Time: {time_slot}\n"

        # Price
        message += f"\n💰 Total: ₹{total_price}\n\n"

        # Confirmation prompt
        message += "Please reply with *YES* to confirm this booking, "
        message += "or *NO* to cancel."

        return message
