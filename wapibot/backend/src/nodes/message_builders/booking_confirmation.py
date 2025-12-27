"""Booking confirmation message builder.

SOLID Principles:
- Single Responsibility: ONLY builds booking confirmation messages
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements MessageBuilder Protocol
"""

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
            state: Current booking state with customer, vehicle, service, appointment/slot

        Returns:
            Formatted confirmation message

        Note:
            Automatically uses 'appointment' field if present, otherwise falls back to 'slot'.
            This handles both manual appointments and slot-based bookings (DRY).

        Example:
            state = {
                "customer": {"first_name": "Rahul"},
                "vehicle": {"brand": "TATA", "model": "Nexon"},
                "selected_service": {"product_name": "Premium Wash"},
                "slot": {"date": "2025-12-29", "time_slot": "07:15 - 08:15"},
                "total_price": 599
            }
        """
        # Get booking details
        customer = state.get("customer", {})
        vehicle = state.get("vehicle", {})
        service = state.get("selected_service", {})

        # Smart fallback: appointment (manual) OR slot (from selection)
        # Handles both None and missing cases (DRY principle)
        appointment = state.get("appointment") or state.get("slot", {})

        total_price = state.get("total_price", 0)

        # Build confirmation message
        message = "📋 *Booking Confirmation*\n\n"

        # Customer details
        first_name = customer.get("first_name", "")
        if first_name:
            message += f"Customer: {first_name}\n"

        # Vehicle details (supports both old and new field names)
        brand = vehicle.get("vehicle_make") or vehicle.get("brand", "")
        model = vehicle.get("vehicle_model") or vehicle.get("model", "")
        number_plate = vehicle.get("vehicle_number") or vehicle.get("number_plate", "")
        if brand and model:
            message += f"Vehicle: {brand} {model}"
            if number_plate:
                message += f" ({number_plate})"
            message += "\n"

        # Service details
        product_name = service.get("product_name", "Service")
        base_price = service.get("base_price", 0)
        message += f"Service: {product_name} - ₹{base_price}\n"

        # Addon details
        selected_addons = state.get("selected_addons", [])
        if selected_addons:
            message += "\n*Add-ons:*\n"
            for addon in selected_addons:
                addon_name = addon.get("addon_name", addon.get("name", "Addon"))
                addon_price = addon.get("unit_price", 0)
                message += f"• {addon_name} - ₹{addon_price}\n"

        # Appointment details
        date = appointment.get("date", "")
        time_slot = appointment.get("time_slot", "")
        if date:
            message += f"\nDate: {date}\n"
        if time_slot:
            message += f"Time: {time_slot}\n"

        # Price breakdown
        message += f"\n💰 Total: ₹{total_price}\n\n"

        # Confirmation prompt
        message += "Please reply with *YES* to confirm this booking, "
        message += "or *NO* to cancel."

        return message
