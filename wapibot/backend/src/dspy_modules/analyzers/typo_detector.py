"""Typo detector using DSPy Chain of Thought.

Detects typos in extracted values and suggests corrections.
"""

import dspy
from typing import Dict, Any

from dspy_signatures.analysis.typo_signature import TypoDetectionSignature
from core.config import settings


class TypoDetector(dspy.Module):
    """Detect typos using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(TypoDetectionSignature)

    def __call__(
        self,
        user_message: str = "",
        field_context: str = "",
        extracted_value: str = ""
    ) -> Dict[str, Any]:
        """Detect typos in extracted value.

        Args:
            user_message: Original user message
            field_context: Field being extracted (e.g., 'name', 'vehicle_brand')
            extracted_value: The extracted value to check

        Returns:
            Dict with has_typo, suggested_correction, confidence
        """
        if not user_message or not extracted_value:
            return {
                "has_typo": False,
                "suggested_correction": "",
                "confidence": settings.confidence_high
            }

        result = self.predictor(
            user_message=user_message,
            field_context=field_context,
            extracted_value=extracted_value
        )

        confidence_map = {
            "low": settings.confidence_low,
            "medium": settings.confidence_medium,
            "high": settings.confidence_high
        }
        confidence_str = getattr(result, "confidence", "medium").lower()
        confidence_float = confidence_map.get(confidence_str, settings.confidence_medium)

        has_typo_str = getattr(result, "has_typo", "no").lower()
        has_typo = has_typo_str in ["yes", "true", "1"]

        return {
            "has_typo": has_typo,
            "suggested_correction": getattr(result, "suggested_correction", "").strip(),
            "confidence": confidence_float,
            "reasoning": getattr(result, "reasoning", "")
        }
