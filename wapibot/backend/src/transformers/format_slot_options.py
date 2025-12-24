"""Format slot options transformer.

SOLID Principles:
- Single Responsibility: ONLY formats appointment slots for display
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements Transformer Protocol
"""

from typing import List, Dict, Any
from workflows.shared.state import BookingState


class FormatSlotOptions:
    """Format appointment slots into user-friendly display format.

    Implements Transformer Protocol for use with transform.node().

    Usage:
        # Format raw slot data into readable options
        await transform.node(
            state,
            FormatSlotOptions(),
            "available_slots",
            "formatted_slots"
        )
    """

    def __call__(self, slots: List[Dict[str, Any]], state: BookingState) -> str:
        """Format slots into readable message.

        Args:
            slots: List of available appointment slots
            state: Current booking state (for context)

        Returns:
            Formatted string with slot options

        Example:
            slots = [
                {"date": "2025-12-25", "time_slot": "10:00 AM - 12:00 PM", "available": True},
                {"date": "2025-12-25", "time_slot": "2:00 PM - 4:00 PM", "available": True},
                {"date": "2025-12-26", "time_slot": "10:00 AM - 12:00 PM", "available": False}
            ]

            result = transformer(slots, state)
            # Returns formatted string with available slots
        """
        if not slots:
            return "Sorry, no appointment slots are available at the moment."

        # Filter only available slots
        available_slots = [slot for slot in slots if slot.get("available", False)]

        if not available_slots:
            return "Sorry, no appointment slots are available at the moment."

        # Build formatted message
        message = "📅 *Available Appointment Slots:*\n\n"

        # Group slots by date
        slots_by_date: Dict[str, List[str]] = {}
        for slot in available_slots:
            date = slot.get("date", "")
            time_slot = slot.get("time_slot", "")

            if date not in slots_by_date:
                slots_by_date[date] = []

            slots_by_date[date].append(time_slot)

        # Format each date group
        for date, time_slots in sorted(slots_by_date.items()):
            message += f"*{date}*\n"
            for idx, time_slot in enumerate(time_slots, 1):
                message += f"  {idx}. {time_slot}\n"
            message += "\n"

        message += "Please reply with your preferred date and time slot."

        return message
