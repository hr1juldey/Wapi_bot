"""Intent classifier using DSPy Chain of Thought.

Classifies user intent to route conversation appropriately.
"""

import dspy
from typing import List, Dict, Any

from dspy_signatures.analysis.intent_signature import IntentClassificationSignature
from utils.history_utils import create_dspy_history
from core.config import settings


class IntentClassifier(dspy.Module):
    """Classify user intent using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(IntentClassificationSignature)

    def __call__(
        self,
        conversation_history: List[Dict[str, str]] = None,
        user_message: str = "",
        context: str = "Classifying user intent"
    ) -> Dict[str, Any]:
        """Classify user intent from message.

        Args:
            conversation_history: List of {"role": "...", "content": "..."}
            user_message: Current user message
            context: Classification context

        Returns:
            Dict with intent, confidence
        """
        if not conversation_history:
            conversation_history = []

        dspy_history = create_dspy_history(conversation_history)

        result = self.predictor(
            conversation_history=dspy_history,
            user_message=user_message,
            context=context
        )

        confidence_map = {
            "low": settings.confidence_low,
            "medium": settings.confidence_medium,
            "high": settings.confidence_high
        }
        confidence_str = getattr(result, "confidence", "medium").lower()
        confidence_float = confidence_map.get(confidence_str, settings.confidence_medium)

        return {
            "intent": getattr(result, "intent", "general_question").lower(),
            "confidence": confidence_float,
            "reasoning": getattr(result, "reasoning", "")
        }
