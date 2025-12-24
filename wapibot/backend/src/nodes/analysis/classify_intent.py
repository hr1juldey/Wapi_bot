"""Intent classification node using DSPy classifier.

Classifies user intent to route conversation flow.
"""

from typing import Dict, Any, List

from dspy_modules.analyzers.intent_classifier import IntentClassifier
from models.booking_state import BookingState


class ClassifyIntentNode:
    """Classify user intent from message."""

    def __init__(self):
        """Initialize intent classifier."""
        self.classifier = IntentClassifier()

    def __call__(
        self,
        state: BookingState,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        context: str = "Classifying user intent"
    ) -> Dict[str, Any]:
        """Classify user intent.

        Args:
            state: Current booking state
            conversation_history: Previous conversation turns
            user_message: Current user message
            context: Classification context (e.g., current state)

        Returns:
            Dict with intent, confidence, reasoning
        """
        if not user_message:
            return {
                "intent": "general_question",
                "confidence": 0.5,
                "reasoning": "No message to classify"
            }

        # Build context from current state
        if state:
            context = f"Current state: {state.get('current_state', 'unknown')}"

        # Call DSPy classifier
        result = self.classifier(
            conversation_history=conversation_history,
            user_message=user_message,
            context=context
        )

        return result


# Singleton instance
classify_intent = ClassifyIntentNode()
