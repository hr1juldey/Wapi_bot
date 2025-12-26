"""Grouped slots display message builder.

SOLID Principles:
- Single Responsibility: ONLY builds formatted grouped slots message
- Open/Closed: Extensible via subclassing if needed
- Dependency Inversion: Implements MessageBuilder Protocol
"""

from typing import List, Dict, Any
from datetime import datetime
from workflows.shared.state import BookingState


class GroupedSlotsBuilder:
    """Build formatted display of slots grouped by time of day.

    Shows slots organized by Morning/Afternoon/Evening for better UX.
    Implements MessageBuilder Protocol for use with send_message.node().

    Usage:
        await send_message.node(state, GroupedSlotsBuilder())
    """

    def __call__(self, state: BookingState) -> str:
        """Build grouped slots display from state.

        Args:
            state: Current booking state with grouped_slots or filtered_slot_options

        Returns:
            Formatted message with slots grouped by time of day

        Example:
            state = {
                "grouped_slots": {
                    "morning": [{"date": "2025-12-30", "start_time": "08:00", ...}],
                    "afternoon": []
                },
                "preferred_date": "2025-12-30"
            }
            builder = GroupedSlotsBuilder()
            message = builder(state)
        """
        grouped_slots = state.get("grouped_slots", {})
        preferred_date = state.get("preferred_date", "")
        preferred_time_range = state.get("preferred_time_range", "")

        # Build header
        date_display = self._format_date_display(preferred_date)
        time_context = f" {preferred_time_range}" if preferred_time_range else ""

        message = f"Here are the{time_context} slots for *{date_display}*:\n\n"

        # Display slots grouped by time of day
        slot_counter = 1
        for time_range in ["morning", "afternoon", "evening"]:
            slots = grouped_slots.get(time_range, [])
            if not slots:
                continue

            # Section header
            message += f"*{time_range.capitalize()}*\n"

            # List slots in this time range
            for slot in slots:
                slot_display = self._format_slot(slot, slot_counter)
                message += f"  {slot_counter}. {slot_display}\n"
                slot_counter += 1

            message += "\n"

        # Footer
        if slot_counter > 1:
            message += "Reply with the slot number to book."
        else:
            message += "Sorry, no slots available for your preference."

        return message

    def _format_date_display(self, date_str: str) -> str:
        """Format date string for display."""
        if not date_str:
            return "available dates"

        try:
            date_obj = datetime.fromisoformat(date_str)
            return date_obj.strftime("%A, %b %d")
        except (ValueError, AttributeError):
            return date_str

    def _format_slot(self, slot: Dict[str, Any], index: int) -> str:
        """Format a single slot for display."""
        start_time = slot.get("start_time", "")
        end_time = slot.get("end_time", "")

        # Convert 24h to 12h format
        start_display = self._format_time_12h(start_time)
        end_display = self._format_time_12h(end_time)

        return f"{start_display} - {end_display}"

    def _format_time_12h(self, time_str: str) -> str:
        """Convert 24h time to 12h format (e.g., '14:00' -> '2:00 PM')."""
        if not time_str:
            return ""

        try:
            # Parse time (format: "HH:MM" or "HH:MM:SS")
            time_parts = time_str.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1])

            # Convert to 12h format
            period = "AM" if hour < 12 else "PM"
            hour_12 = hour % 12
            if hour_12 == 0:
                hour_12 = 12

            return f"{hour_12}:{minute:02d} {period}"

        except (ValueError, IndexError):
            return time_str
