"""Typo detection node using DSPy detector.

Detects typos in extracted values and suggests corrections.
"""

from typing import Dict, Any

from dspy_modules.analyzers.typo_detector import TypoDetector
from models.booking_state import BookingState


class DetectTyposNode:
    """Detect typos in extracted field values."""

    def __init__(self):
        """Initialize typo detector."""
        self.detector = TypoDetector()

    def __call__(
        self,
        state: BookingState,
        user_message: str,
        field_name: str,
        extracted_value: str
    ) -> Dict[str, Any]:
        """Detect typos in extracted value.

        Args:
            state: Current booking state
            user_message: Original user message
            field_name: Field being checked (e.g., 'name', 'vehicle_brand')
            extracted_value: The extracted value to check

        Returns:
            Dict with has_typo, suggested_correction, confidence, reasoning
        """
        if not extracted_value or not user_message:
            return {
                "has_typo": False,
                "suggested_correction": "",
                "confidence": 0.9,
                "reasoning": "No value to check"
            }

        # Call DSPy typo detector
        result = self.detector(
            user_message=user_message,
            field_context=field_name,
            extracted_value=extracted_value
        )

        return result


# Singleton instance
detect_typos = DetectTyposNode()
