"""Goal decomposer atomic node - aPFC-like function."""

import logging
from typing import Protocol
from models.brain_state import BrainState

logger = logging.getLogger(__name__)


class GoalDecomposer(Protocol):
    """Protocol for goal decomposition modules."""

    def forward(self, user_message: str, predicted_intent: str, booking_state: dict) -> dict:
        """Decompose user goal into sub-goals.

        Returns:
            Dict with sub_goals (list), required_info (list), reasoning
        """
        ...


def node(
    state: BrainState,
    decomposer: GoalDecomposer
) -> BrainState:
    """Atomic node: Decompose user goal into actionable sub-goals.

    Uses aPFC-like function to decompose:
    - User intent into immediate sub-goals
    - Required information to gather
    - Execution steps

    Args:
        state: Current brain state
        decomposer: GoalDecomposer implementation (DSPy module)

    Returns:
        Updated state with decomposed_goals field
    """
    try:
        # Extract context
        user_message = state.get("user_message", "")
        predicted_intent = state.get("predicted_intent", "unclear")

        # Build booking state summary
        booking_state = {
            "has_profile": state.get("profile_complete", False),
            "has_vehicle": state.get("vehicle_complete", False),
            "has_service": state.get("service_selected", False),
            "has_slot": state.get("slot_selected", False)
        }

        if not user_message or predicted_intent == "unclear":
            state["decomposed_goals"] = ["continue_conversation"]
            return state

        # Run goal decomposition
        result = decomposer.forward(
            user_message=user_message,
            predicted_intent=predicted_intent,
            booking_state=booking_state
        )

        # Update state
        state["decomposed_goals"] = result.get("sub_goals", ["continue_conversation"])
        state["required_info"] = result.get("required_info", [])

        logger.info(f"Goals decomposed: {state['decomposed_goals']}")

        return state

    except Exception as e:
        logger.error(f"Goal decomposer failed: {e}")
        state["decomposed_goals"] = ["continue_conversation"]
        state["required_info"] = []
        return state
