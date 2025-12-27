"""Message personalizer DSPy module - Shadow mode suggestions."""

import dspy
import logging

logger = logging.getLogger(__name__)


class PersonalizationSignature(dspy.Signature):
    """Signature for message personalization."""

    base_message: str = dspy.InputField(desc="Original message to personalize")
    customer_profile: str = dspy.InputField(desc="Customer profile and preferences")
    conversation_history: str = dspy.InputField(desc="Recent conversation context")

    personalized_message: str = dspy.OutputField(desc="Personalized version of message")
    modifications: str = dspy.OutputField(desc="Comma-separated list of modifications made")
    confidence: float = dspy.OutputField(desc="Confidence score (0.0-1.0)")
    reasoning: str = dspy.OutputField(desc="Why these personalizations were chosen")


class MessagePersonalizer(dspy.Module):
    """DSPy module for message personalization.

    Suggests modifications to messages based on:
    - Customer communication style
    - Conversation tone
    - User preferences
    """

    def __init__(self):
        """Initialize personalizer module."""
        super().__init__()
        self.personalizer = dspy.ChainOfThought(PersonalizationSignature)

    def forward(
        self,
        base_message: str,
        customer_profile: dict,
        conversation_history: list
    ) -> dict:
        """Generate personalization suggestion.

        Args:
            base_message: Original message
            customer_profile: Customer data
            conversation_history: Recent messages

        Returns:
            Dict with personalized_message, modifications, confidence, reasoning
        """
        # Format customer profile
        profile_str = f"Name: {customer_profile.get('first_name', 'Unknown')}, "
        profile_str += f"Communication style: {customer_profile.get('communication_style', 'professional')}"

        # Format history (last 3 messages)
        history_str = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')[:100]}"
            for msg in conversation_history[-3:]
        ])

        try:
            # Run personalization
            result = self.personalizer(
                base_message=base_message,
                customer_profile=profile_str,
                conversation_history=history_str
            )

            # Parse modifications
            modifications_list = [
                mod.strip()
                for mod in result.modifications.split(",")
                if mod.strip()
            ]

            # Parse confidence
            try:
                confidence = float(result.confidence)
                confidence = max(min(confidence, 1.0), 0.0)  # Clamp to [0, 1]
            except (ValueError, AttributeError):
                confidence = 0.5

            return {
                "personalized_message": result.personalized_message,
                "modifications": modifications_list,
                "confidence": confidence,
                "reasoning": result.reasoning
            }

        except Exception as e:
            logger.error(f"Personalization failed: {e}")
            return {
                "personalized_message": base_message,
                "modifications": [],
                "confidence": 0.0,
                "reasoning": f"Error: {e}"
            }
