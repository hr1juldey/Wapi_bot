"""Goal decomposer module - aPFC-like function (anterior Prefrontal Cortex)."""

import logging
from typing import Dict, Any
import dspy
from dspy_signatures.brain.goal_decomposition_signature import GoalDecompositionSignature

logger = logging.getLogger(__name__)


class GoalDecomposer(dspy.Module):
    """Decomposes user goals into actionable sub-goals.

    Breaks down complex user intents into:
    - Immediate sub-goals (what to do next)
    - Required information (what's missing)
    - Execution steps (how to achieve goal)
    """

    def __init__(self):
        """Initialize goal decomposer with ChainOfThought."""
        super().__init__()
        self.decomposer = dspy.ChainOfThought(GoalDecompositionSignature)

    def forward(
        self,
        user_message: str,
        predicted_intent: str,
        booking_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Decompose user goal into sub-goals.

        Args:
            user_message: Current user message
            predicted_intent: Predicted user intent
            booking_state: Current booking progress

        Returns:
            Dict with sub_goals (list), required_info (list), reasoning
        """
        try:
            # Format booking state
            state_str = f"Profile: {booking_state.get('has_profile', False)}, "
            state_str += f"Vehicle: {booking_state.get('has_vehicle', False)}, "
            state_str += f"Service: {booking_state.get('has_service', False)}, "
            state_str += f"Slot: {booking_state.get('has_slot', False)}"

            # Decompose with reasoning
            result = self.decomposer(
                user_message=user_message,
                predicted_intent=predicted_intent,
                booking_state=state_str
            )

            # Parse sub-goals (comma-separated string to list)
            sub_goals = [
                goal.strip()
                for goal in result.sub_goals.split(",")
                if goal.strip()
            ]

            # Parse required info
            required_info = [
                info.strip()
                for info in result.required_info.split(",")
                if info.strip()
            ]

            return {
                "sub_goals": sub_goals,
                "required_info": required_info,
                "reasoning": result.reasoning
            }

        except Exception as e:
            logger.error(f"Goal decomposition failed: {e}")
            return {
                "sub_goals": ["continue_conversation"],
                "required_info": [],
                "reasoning": f"Error: {str(e)}"
            }
