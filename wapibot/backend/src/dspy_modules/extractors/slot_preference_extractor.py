"""Slot preference extractor using DSPy Chain of Thought.

Extracts date and time range preferences from user messages.
Supports multilingual inputs (English, Hindi, Bengali, Hinglish, Benglish).
"""

import dspy
from typing import List, Dict, Any

from dspy_signatures.extraction.slot_preference_signature import SlotPreferenceSignature
from utils.history_utils import create_dspy_history
from utils.validation_utils import map_confidence_to_float


class SlotPreferenceExtractor(dspy.Module):
    """Extract slot preferences using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(SlotPreferenceSignature)

    def __call__(
        self,
        conversation_history: List[Dict[str, str]] | None = None,
        user_message: str = "",
        context: str = "Asking when to book appointment"
    ) -> Dict[str, Any]:
        """Extract slot preferences from user message.

        Args:
            conversation_history: List of {"role": "...", "content": "..."}
            user_message: Current user message
            context: Extraction context

        Returns:
            Dict with preferred_date, preferred_time_range, confidence
        """
        if not conversation_history:
            conversation_history = []

        dspy_history = create_dspy_history(conversation_history)

        result = self.predictor(
            conversation_history=dspy_history,
            user_message=user_message,
            context=context
        )

        confidence_str = getattr(result, "confidence", "medium")
        confidence_float = map_confidence_to_float(confidence_str)

        return {
            "preferred_date": getattr(result, "preferred_date", "").strip(),
            "preferred_time_range": getattr(result, "preferred_time_range", "").strip(),
            "confidence": confidence_float
        }
