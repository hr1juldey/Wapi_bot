"""Email extractor using DSPy Chain of Thought.

Extracts email addresses with format validation.
"""

import dspy
from typing import List, Dict, Any

from dspy_signatures.extraction.email_signature import EmailExtractionSignature
from utils.history_utils import create_dspy_history
from utils.validation_utils import map_confidence_to_float


class EmailExtractor(dspy.Module):
    """Extract email address using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(EmailExtractionSignature)

    def __call__(
        self,
        conversation_history: List[Dict[str, str]] = None,
        user_message: str = "",
        context: str = "Collecting email for booking confirmation"
    ) -> Dict[str, Any]:
        """Extract email from user message.

        Args:
            conversation_history: List of {"role": "...", "content": "..."}
            user_message: Current user message
            context: Extraction context

        Returns:
            Dict with email, confidence
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
            "email": getattr(result, "email", "").strip(),
            "confidence": confidence_float
        }
