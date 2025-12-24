"""Typo detection service.

Orchestrates typo detection across extracted fields.
"""

from typing import Dict, Any, List

from nodes.analysis.detect_typos import detect_typos
from models.booking_state import BookingState


class TypoDetectionService:
    """Detect typos across booking fields."""

    # Fields to check for typos
    CHECKABLE_FIELDS = [
        ("customer.first_name", "First name"),
        ("customer.last_name", "Last name"),
        ("customer.email", "Email address"),
        ("vehicle.brand", "Vehicle brand"),
        ("vehicle.model", "Vehicle model"),
        ("appointment.service_type", "Service type")
    ]

    def __init__(self):
        """Initialize typo detection service."""
        self.detector = detect_typos

    def detect_all_typos(
        self,
        state: BookingState,
        user_message: str
    ) -> List[Dict[str, Any]]:
        """Detect typos across all checkable fields.

        Args:
            state: Current booking state
            user_message: Original user message

        Returns:
            List of typo detections with corrections
        """
        typos_found = []

        for field_path, field_label in self.CHECKABLE_FIELDS:
            # Get field value
            value = self._get_field_value(state, field_path)
            if not value:
                continue

            # Check for typos
            result = self.detector(
                state=state,
                user_message=user_message,
                field_name=field_label,
                extracted_value=value
            )

            if result["has_typo"] and result["suggested_correction"]:
                typos_found.append({
                    "field": field_path,
                    "field_label": field_label,
                    "original": value,
                    "suggested": result["suggested_correction"],
                    "confidence": result["confidence"]
                })

        return typos_found

    def _get_field_value(self, state: Dict[str, Any], field_path: str) -> str:
        """Get field value from state.

        Args:
            state: Booking state
            field_path: Dot-notation path

        Returns:
            Field value or empty string
        """
        parts = field_path.split(".")
        current = state

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return ""

        return str(current) if current else ""


# Singleton instance
typo_detection_service = TypoDetectionService()
