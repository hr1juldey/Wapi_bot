"""Quality evaluator module - OFC-like function (Orbitofrontal Cortex)."""

import logging
from typing import List, Dict, Any
import dspy
from dspy_signatures.brain.state_evaluation_signature import StateEvaluationSignature

logger = logging.getLogger(__name__)


class QualityEvaluator(dspy.Module):
    """Evaluates conversation quality and user satisfaction.

    Evaluates:
    - Booking completeness (0.0-1.0)
    - User satisfaction (0.0-1.0)
    - Conversation quality (0.0-1.0)
    - Overall score
    """

    def __init__(self):
        """Initialize quality evaluator with ChainOfThought."""
        super().__init__()
        self.evaluator = dspy.ChainOfThought(StateEvaluationSignature)

    def forward(
        self,
        conversation_history: List[Dict[str, str]],
        booking_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate conversation quality.

        Args:
            conversation_history: Previous messages [{role, content}]
            booking_state: Current booking progress

        Returns:
            Dict with quality_score, completeness, satisfaction, reasoning
        """
        try:
            # Format history
            history_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-10:]  # More context for quality
            ])

            # Format booking state
            state_str = f"Profile: {booking_state.get('has_profile', False)}, "
            state_str += f"Vehicle: {booking_state.get('has_vehicle', False)}, "
            state_str += f"Service: {booking_state.get('has_service', False)}, "
            state_str += f"Slot: {booking_state.get('has_slot', False)}"

            # Evaluate with reasoning
            result = self.evaluator(
                conversation_history=history_str,
                booking_state=state_str
            )

            return {
                "quality_score": result.quality_score,
                "completeness": result.completeness,
                "user_satisfaction": result.user_satisfaction,
                "reasoning": result.reasoning
            }

        except Exception as e:
            logger.error(f"Quality evaluation failed: {e}")
            return {
                "quality_score": 0.5,
                "completeness": 0.0,
                "user_satisfaction": 0.5,
                "reasoning": f"Error: {str(e)}"
            }
