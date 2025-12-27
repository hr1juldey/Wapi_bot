"""Personalize message atomic node - Shadow mode suggestions only.

CRITICAL: Suggestions are LOGGED ONLY, never sent to customers.
"""

import logging
import uuid
from typing import Protocol
from models.brain_state import BrainState

logger = logging.getLogger(__name__)


class Personalizer(Protocol):
    """Protocol for message personalization modules."""

    def __call__(
        self,
        base_message: str,
        customer_profile: dict,
        conversation_history: list
    ) -> dict:
        """Generate personalized message suggestion.

        Returns:
            Dict with personalized_message, modifications, confidence, reasoning
        """
        ...


def node(
    state: BrainState,
    personalizer: Personalizer
) -> BrainState:
    """Atomic node: Suggest personalized message modifications.

    CRITICAL: Suggestions are LOGGED ONLY, never sent to customers.

    The brain observes:
    - Baseline message that will be sent
    - Customer profile and preferences
    - Conversation history and tone

    Then suggests modifications like:
    - Adjust formality (casual vs professional)
    - Add/remove emojis
    - Change tone (friendly, urgent, apologetic)
    - Adapt vocabulary complexity

    Args:
        state: Brain state with proposed_response
        personalizer: Personalizer implementation (DSPy module)

    Returns:
        Updated state with personalization_suggestion field
    """
    try:
        proposed_response = state.get("proposed_response", "")

        if not proposed_response:
            logger.info("No response to personalize")
            state["personalization_suggestion"] = None
            return state

        # Extract context
        customer = state.get("customer", {})
        history = state.get("history", [])

        # Generate personalization suggestion
        suggestion = personalizer(
            base_message=proposed_response,
            customer_profile=customer,
            conversation_history=history
        )

        # Create suggestion record
        suggestion_record = {
            "suggestion_id": str(uuid.uuid4()),
            "conversation_id": state.get("conversation_id", "unknown"),
            "original_message": proposed_response,
            "personalized_message": suggestion.get("personalized_message", ""),
            "modifications": suggestion.get("modifications", []),
            "confidence": suggestion.get("confidence", 0.0),
            "reasoning": suggestion.get("reasoning", ""),
            "customer_profile": customer
        }

        # Log suggestion (NEVER modify actual response)
        state["personalization_suggestion"] = suggestion_record

        # CRITICAL: Do NOT modify state["response"]
        # The baseline message is what gets sent to customer

        logger.info(
            f"💡 Personalization suggested (shadow only): "
            f"{len(suggestion.get('modifications', []))} modifications, "
            f"confidence={suggestion.get('confidence', 0.0):.2f}"
        )

        return state

    except Exception as e:
        logger.error(f"Personalization failed: {e}")
        state["personalization_suggestion"] = None
        return state
