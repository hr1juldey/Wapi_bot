"""State evaluator atomic node - OFC-like function."""

import logging
from typing import Protocol
from models.brain_state import BrainState

logger = logging.getLogger(__name__)


class QualityEvaluator(Protocol):
    """Protocol for quality evaluation modules."""

    def forward(self, conversation_history: list, booking_state: dict) -> dict:
        """Evaluate conversation quality.

        Returns:
            Dict with quality_score, completeness, user_satisfaction, reasoning
        """
        ...


def node(
    state: BrainState,
    evaluator: QualityEvaluator
) -> BrainState:
    """Atomic node: Evaluate conversation quality and satisfaction.

    Uses OFC-like function to evaluate:
    - Booking completeness (0.0-1.0)
    - User satisfaction (0.0-1.0)
    - Overall conversation quality (0.0-1.0)

    Args:
        state: Current brain state
        evaluator: QualityEvaluator implementation (DSPy module)

    Returns:
        Updated state with conversation_quality field
    """
    try:
        # Extract context
        history = state.get("history", [])

        # Build booking state summary
        booking_state = {
            "has_profile": state.get("profile_complete", False),
            "has_vehicle": state.get("vehicle_complete", False),
            "has_service": state.get("service_selected", False),
            "has_slot": state.get("slot_selected", False)
        }

        # Run quality evaluation
        result = evaluator.forward(
            conversation_history=history,
            booking_state=booking_state
        )

        # Update state
        state["conversation_quality"] = result.get("quality_score", 0.5)
        state["booking_completeness"] = result.get("completeness", 0.0)
        state["user_satisfaction"] = result.get("user_satisfaction", 0.5)

        logger.info(
            f"Quality: {state['conversation_quality']:.2f}, "
            f"Completeness: {state['booking_completeness']:.2f}, "
            f"Satisfaction: {state['user_satisfaction']:.2f}"
        )

        return state

    except Exception as e:
        logger.error(f"State evaluator failed: {e}")
        state["conversation_quality"] = 0.5
        state["booking_completeness"] = 0.0
        state["user_satisfaction"] = 0.5
        return state
