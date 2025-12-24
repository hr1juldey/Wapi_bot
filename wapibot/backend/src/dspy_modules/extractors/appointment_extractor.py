"""Appointment details extractor using DSPy Chain of Thought.

Extracts date, time, and service type from conversation.
"""

import dspy
from typing import List, Dict, Any

from dspy_signatures.extraction.appointment_signature import AppointmentExtractionSignature
from utils.history_utils import create_dspy_history
from utils.validation_utils import map_confidence_to_float


class AppointmentExtractor(dspy.Module):
    """Extract appointment details using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(AppointmentExtractionSignature)

    def __call__(
        self,
        conversation_history: List[Dict[str, str]] = None,
        user_message: str = "",
        context: str = "Scheduling service appointment"
    ) -> Dict[str, Any]:
        """Extract appointment details from user message.

        Args:
            conversation_history: List of {"role": "...", "content": "..."}
            user_message: Current user message
            context: Extraction context

        Returns:
            Dict with date_str, time_preference, service_type, confidence
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
            "date_str": getattr(result, "date_str", "").strip(),
            "time_preference": getattr(result, "time_preference", "").strip(),
            "service_type": getattr(result, "service_type", "").strip(),
            "confidence": confidence_float
        }
