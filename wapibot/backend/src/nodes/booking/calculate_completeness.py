"""Completeness calculation node.

Calculates scratchpad completeness and determines if ready for confirmation.
"""

from typing import Dict, Any

from models.booking_state import BookingState
from services.completeness_service import completeness_service


class CalculateCompletenessNode:
    """Calculate booking state completeness."""

    def __init__(self):
        """Initialize completeness calculator."""
        self.service = completeness_service

    def __call__(self, state: BookingState) -> Dict[str, Any]:
        """Calculate completeness metrics.

        Args:
            state: Current booking state

        Returns:
            Dict with completeness, is_complete, missing_fields
        """
        if not state:
            return {
                "completeness": 0.0,
                "is_complete": False,
                "missing_fields": list(self.service.REQUIRED_FIELDS)
            }

        # Calculate completeness score
        completeness = self.service.calculate_completeness(state)
        is_complete = self.service.is_complete(state)

        # Identify missing required fields
        missing_fields = []
        for field_path in self.service.REQUIRED_FIELDS:
            if not self.service._is_field_filled(state, field_path):
                missing_fields.append(field_path)

        return {
            "completeness": completeness,
            "is_complete": is_complete,
            "missing_fields": missing_fields
        }


# Singleton instance
calculate_completeness = CalculateCompletenessNode()
