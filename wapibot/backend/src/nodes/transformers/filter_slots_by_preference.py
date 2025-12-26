"""Filter slots by date and time preferences transformer.

SOLID Principles:
- Single Responsibility: ONLY filters slots by user preferences
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements Transformer Protocol
"""

from typing import List, Dict, Any
from datetime import datetime
from workflows.shared.state import BookingState


class FilterSlotsByPreference:
    """Filter appointment slots based on date and time range preferences.

    Implements Transformer Protocol for use with transform.node().

    Usage:
        # Filter slots to match preferred date and/or time range
        await transform.node(
            state,
            FilterSlotsByPreference(),
            "slot_options",
            "filtered_slot_options"
        )
    """

    def __call__(self, slots: List[Dict[str, Any]], state: BookingState) -> List[Dict[str, Any]]:
        """Filter slots by preferences from state.

        Args:
            slots: List of all available slots
            state: Current booking state with preferred_date and/or preferred_time_range

        Returns:
            Filtered list of slots matching preferences

        Example:
            slots = [
                {"date": "2025-12-28", "start_time": "08:00", "end_time": "09:00"},
                {"date": "2025-12-28", "start_time": "14:00", "end_time": "15:00"},
                {"date": "2025-12-29", "start_time": "09:00", "end_time": "10:00"},
            ]
            state = {"preferred_date": "2025-12-28", "preferred_time_range": "morning"}

            result = transformer(slots, state)
            # Returns only the morning slot on 2025-12-28
        """
        # Get preferences from state
        preferred_date = state.get("preferred_date")
        preferred_time_range = state.get("preferred_time_range")

        # If no preferences, return all slots
        if not preferred_date and not preferred_time_range:
            return slots

        filtered = slots

        # Filter by date if specified
        if preferred_date:
            filtered = [
                slot for slot in filtered
                if slot.get("date") == preferred_date
            ]

        # Filter by time range if specified
        if preferred_time_range:
            filtered = [
                slot for slot in filtered
                if self._slot_matches_time_range(slot, preferred_time_range)
            ]

        return filtered

    def _slot_matches_time_range(self, slot: Dict[str, Any], time_range: str) -> bool:
        """Check if slot's start time matches the preferred time range.

        Args:
            slot: Slot dict with start_time field
            time_range: "morning", "afternoon", or "evening"

        Returns:
            True if slot's start time falls within the time range
        """
        start_time_str = slot.get("start_time", "")
        if not start_time_str:
            return False

        try:
            # Parse start time (format: "HH:MM" or "HH:MM:SS")
            time_parts = start_time_str.split(":")
            hour = int(time_parts[0])

            # Time range definitions (matching models/extraction_patterns.py)
            if time_range == "morning":
                return 6 <= hour < 12
            elif time_range == "afternoon":
                return 12 <= hour < 17
            elif time_range == "evening":
                return 17 <= hour < 21
            else:
                return False

        except (ValueError, IndexError):
            return False
