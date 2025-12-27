"""Escalation message builder for human handoff."""

from workflows.shared.state import BookingState


class EscalationMessageBuilder:
    """Build human escalation handoff message.

    Implements MessageBuilder Protocol for use with send_message.node().
    """

    def __call__(self, state: BookingState) -> str:
        """Build escalation message.

        Args:
            state: Current booking state with escalation_reason

        Returns:
            Handoff message with support contact
        """
        from core.config import get_settings

        settings = get_settings()
        support_number = settings.support_whatsapp_number

        reason = state.get("escalation_reason", "complex_request")

        messages = {
            "price_negotiation": "Let me connect you with our team for custom pricing.",
            "technical_issue": "Our technical team will assist you shortly.",
            "complex_request": "Let me transfer you to a specialist.",
            "general": "Connecting you with our support team."
        }

        reason_text = messages.get(reason, messages["general"])

        return (
            f"🤝 {reason_text}\n\n"
            f"Please contact our support team:\n"
            f"📱 WhatsApp: {support_number}\n\n"
            f"We'll get back to you as soon as possible!"
        )
