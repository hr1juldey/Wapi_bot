"""Intent predictor module - OFC-like function (Orbitofrontal Cortex)."""

import logging
from typing import List, Dict, Any
import dspy
from dspy_signatures.brain.intent_prediction_signature import IntentPredictionSignature

logger = logging.getLogger(__name__)


class IntentPredictor(dspy.Module):
    """Predicts user intent and next action using fast prediction.

    Intent types:
    - continue_booking: User wants to continue with booking
    - provide_info: User is providing requested information
    - ask_question: User has a question
    - change_selection: User wants to change previous choice
    - cancel: User wants to cancel
    - unclear: Intent is unclear
    """

    def __init__(self):
        """Initialize intent predictor with Predict (fast, no reasoning)."""
        super().__init__()
        self.predictor = dspy.Predict(IntentPredictionSignature)

    def forward(
        self,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        booking_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict user intent from message.

        Args:
            conversation_history: Previous messages [{role, content}]
            user_message: Current user message
            booking_state: Current booking progress

        Returns:
            Dict with predicted_intent, confidence
        """
        try:
            # Format history
            history_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-5:]
            ])

            # Format booking state
            state_str = f"Profile: {booking_state.get('has_profile', False)}, "
            state_str += f"Vehicle: {booking_state.get('has_vehicle', False)}, "
            state_str += f"Service: {booking_state.get('has_service', False)}"

            # Fast prediction (no ChainOfThought)
            result = self.predictor(
                conversation_history=history_str,
                user_message=user_message,
                booking_state=state_str
            )

            return {
                "predicted_intent": result.predicted_intent.strip().lower(),
                "confidence": result.confidence
            }

        except Exception as e:
            logger.error(f"Intent prediction failed: {e}")
            return {
                "predicted_intent": "unclear",
                "confidence": 0.0
            }
