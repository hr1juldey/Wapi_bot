"""Phone number extractor using DSPy Chain of Thought.

Extracts Indian phone numbers with confidence scoring.
"""

import dspy
from typing import List, Dict, Any

from dspy_signatures.extraction.phone_signature import PhoneExtractionSignature
from utils.history_utils import create_dspy_history
from utils.validation_utils import map_confidence_to_float


class PhoneExtractor(dspy.Module):
    """Extract phone number using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(PhoneExtractionSignature)

    def __call__(
        self,
        conversation_history: List[Dict[str, str]] = None,
        user_message: str = "",
        context: str = "Collecting contact number for booking"
    ) -> Dict[str, Any]:
        """Extract phone number from user message.

        Args:
            conversation_history: List of {"role": "...", "content": "..."}
            user_message: Current user message
            context: Extraction context

        Returns:
            Dict with phone_number, confidence

        Example:
            >>> extractor = PhoneExtractor()
            >>> result = extractor([], "My number is 9876543210")
            >>> result["phone_number"]
            "9876543210"
        """
        if not conversation_history:
            conversation_history = []

        dspy_history = create_dspy_history(conversation_history)

        # Call DSPy predictor
        result = self.predictor(
            conversation_history=dspy_history,
            user_message=user_message,
            context=context
        )

        # Map confidence string to float
        confidence_str = getattr(result, "confidence", "medium")
        confidence_float = map_confidence_to_float(confidence_str)

        return {
            "phone_number": getattr(result, "phone_number", "").strip(),
            "confidence": confidence_float,
            "reasoning": getattr(result, "reasoning", "")
        }
