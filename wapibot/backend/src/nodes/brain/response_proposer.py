"""Response proposer atomic node - dlPFC-like function."""

import logging
from typing import Protocol
from models.brain_state import BrainState

logger = logging.getLogger(__name__)


class ResponseGenerator(Protocol):
    """Protocol for response generation modules."""

    def forward(
        self,
        conversation_history: list,
        user_message: str,
        sub_goals: list,
        booking_state: dict
    ) -> dict:
        """Generate optimal response.

        Returns:
            Dict with proposed_response, confidence, reasoning
        """
        ...


def node(
    state: BrainState,
    generator: ResponseGenerator
) -> BrainState:
    """Atomic node: Generate optimal response using BestOfN + Refine.

    Uses dlPFC-like function to:
    - Generate multiple candidate responses
    - Evaluate and select best candidate
    - Refine selected response

    Args:
        state: Current brain state
        generator: ResponseGenerator implementation (DSPy module)

    Returns:
        Updated state with proposed_response field
    """
    try:
        # Extract context
        history = state.get("history", [])
        user_message = state.get("user_message", "")
        sub_goals = state.get("decomposed_goals", ["continue_conversation"])

        # Build booking state summary
        booking_state = {
            "has_profile": state.get("profile_complete", False),
            "has_vehicle": state.get("vehicle_complete", False),
            "has_service": state.get("service_selected", False),
            "has_slot": state.get("slot_selected", False)
        }

        if not user_message:
            state["proposed_response"] = None
            return state

        # Run response generation (BestOfN + Refine)
        result = generator.forward(
            conversation_history=history,
            user_message=user_message,
            sub_goals=sub_goals,
            booking_state=booking_state
        )

        # Update state
        state["proposed_response"] = result.get("proposed_response")
        state["brain_confidence"] = result.get("confidence", 0.0)

        logger.info(
            f"Response proposed (confidence: {result.get('confidence', 0.0):.2f}): "
            f"{result.get('proposed_response', '')[:50]}..."
        )

        return state

    except Exception as e:
        logger.error(f"Response proposer failed: {e}")
        state["proposed_response"] = None
        return state
