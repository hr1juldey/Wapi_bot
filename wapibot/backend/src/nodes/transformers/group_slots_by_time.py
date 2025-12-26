"""Group slots by time of day transformer.

SOLID Principles:
- Single Responsibility: ONLY groups slots by time range
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements Transformer Protocol
"""

from typing import List, Dict, Any
from workflows.shared.state import BookingState


class GroupSlotsByTime:
    """Group appointment slots by time of day (morning/afternoon/evening).

    Implements Transformer Protocol for use with transform.node().

    Usage:
        # Group slots by time of day
        await transform.node(
            state,
            GroupSlotsByTime(),
            "filtered_slot_options",
            "grouped_slots"
        )
    """

    def __call__(self, slots: List[Dict[str, Any]], state: BookingState) -> Dict[str, List[Dict[str, Any]]]:
        """Group slots by time of day.

        Args:
            slots: List of slots to group
            state: Current booking state (not used, but required by Protocol)

        Returns:
            Dict with keys "morning", "afternoon", "evening" and lists of slots

        Example:
            slots = [
                {"date": "2025-12-28", "start_time": "08:00"},
                {"date": "2025-12-28", "start_time": "14:00"},
                {"date": "2025-12-28", "start_time": "18:00"},
            ]

            result = transformer(slots, state)
            # Returns: {
            #   "morning": [{"date": "2025-12-28", "start_time": "08:00"}],
            #   "afternoon": [{"date": "2025-12-28", "start_time": "14:00"}],
            #   "evening": [{"date": "2025-12-28", "start_time": "18:00"}]
            # }
        """
        grouped = {
            "morning": [],
            "afternoon": [],
            "evening": []
        }

        for slot in slots:
            time_range = self._get_time_range(slot)
            if time_range:
                grouped[time_range].append(slot)

        return grouped

    def _get_time_range(self, slot: Dict[str, Any]) -> str:
        """Determine which time range a slot belongs to.

        Args:
            slot: Slot dict with start_time field

        Returns:
            "morning", "afternoon", "evening", or "" if unable to determine
        """
        start_time_str = slot.get("start_time", "")
        if not start_time_str:
            return ""

        try:
            # Parse start time (format: "HH:MM" or "HH:MM:SS")
            time_parts = start_time_str.split(":")
            hour = int(time_parts[0])

            # Time range definitions (matching models/extraction_patterns.py)
            if 6 <= hour < 12:
                return "morning"
            elif 12 <= hour < 17:
                return "afternoon"
            elif 17 <= hour < 21:
                return "evening"
            else:
                return ""  # Outside business hours

        except (ValueError, IndexError):
            return ""
