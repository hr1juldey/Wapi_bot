"""Completeness calculation service.

Calculates scratchpad completeness score based on required fields.
"""

from typing import Dict, Any
from models.booking_state import BookingState


class CompletenessService:
    """Calculate booking state completeness."""

    # Required fields for complete booking
    REQUIRED_FIELDS = [
        "customer.first_name",
        "customer.phone_number",
        "vehicle.brand",
        "appointment.date.parsed_date",
        "appointment.time_slot",
        "appointment.service_type"
    ]

    # Optional fields that increase completeness
    OPTIONAL_FIELDS = [
        "customer.last_name",
        "customer.email",
        "vehicle.model",
        "vehicle.year"
    ]

    def calculate_completeness(self, state: BookingState) -> float:
        """Calculate completeness score (0.0 to 1.0).

        Args:
            state: Current booking state

        Returns:
            Float between 0.0 and 1.0
        """
        if not state:
            return 0.0

        required_filled = 0
        required_total = len(self.REQUIRED_FIELDS)

        optional_filled = 0
        optional_total = len(self.OPTIONAL_FIELDS)

        # Check required fields (80% weight)
        for field_path in self.REQUIRED_FIELDS:
            if self._is_field_filled(state, field_path):
                required_filled += 1

        # Check optional fields (20% weight)
        for field_path in self.OPTIONAL_FIELDS:
            if self._is_field_filled(state, field_path):
                optional_filled += 1

        # Calculate weighted score
        required_score = (required_filled / required_total) * 0.8
        optional_score = (optional_filled / optional_total) * 0.2

        total_score = required_score + optional_score

        return round(total_score, 2)

    def is_complete(self, state: BookingState) -> bool:
        """Check if all required fields are filled.

        Args:
            state: Current booking state

        Returns:
            True if all required fields filled
        """
        if not state:
            return False

        for field_path in self.REQUIRED_FIELDS:
            if not self._is_field_filled(state, field_path):
                return False

        return True

    def _is_field_filled(self, state: Dict[str, Any], field_path: str) -> bool:
        """Check if a field is filled (not None, not empty string).

        Args:
            state: Booking state dict
            field_path: Dot-notation path (e.g., "customer.first_name")

        Returns:
            True if field has a valid value
        """
        parts = field_path.split(".")
        current = state

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False

        # Check if value is valid
        if current is None:
            return False
        if isinstance(current, str) and current.strip() == "":
            return False

        return True


# Singleton instance
completeness_service = CompletenessService()
