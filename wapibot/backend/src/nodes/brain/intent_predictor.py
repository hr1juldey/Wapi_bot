"""Intent predictor atomic node - OFC-like function."""

import logging
from typing import Protocol
from models.brain_state import BrainState

logger = logging.getLogger(__name__)


class IntentPredictor(Protocol):
    """Protocol for intent prediction modules."""

    def forward(self, conversation_history: list, user_message: str, booking_state: dict) -> dict:
        """Predict user intent.

        Returns:
            Dict with predicted_intent, confidence
        """
        ...


def node(
    state: BrainState,
    predictor: IntentPredictor
) -> BrainState:
    """Atomic node: Predict user intent and next action.

    Uses OFC-like function to predict:
    - continue_booking, provide_info, ask_question
    - change_selection, cancel, unclear

    Args:
        state: Current brain state
        predictor: IntentPredictor implementation (DSPy module)

    Returns:
        Updated state with predicted_intent field
    """
    try:
        # Extract context
        history = state.get("history", [])
        user_message = state.get("user_message", "")

        # Build booking state summary
        booking_state = {
            "has_profile": state.get("profile_complete", False),
            "has_vehicle": state.get("vehicle_complete", False),
            "has_service": state.get("service_selected", False),
            "has_slot": state.get("slot_selected", False)
        }

        if not user_message:
            state["predicted_intent"] = "unclear"
            return state

        # Run intent prediction
        result = predictor.forward(
            conversation_history=history,
            user_message=user_message,
            booking_state=booking_state
        )

        # Update state
        state["predicted_intent"] = result.get("predicted_intent", "unclear")
        state["brain_confidence"] = result.get("confidence", 0.0)

        logger.info(f"Intent predicted: {state['predicted_intent']} (confidence: {result.get('confidence', 0.0)})")

        return state

    except Exception as e:
        logger.error(f"Intent predictor failed: {e}")
        state["predicted_intent"] = "unclear"
        return state
