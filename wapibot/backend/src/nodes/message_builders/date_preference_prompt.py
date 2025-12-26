"""Date preference prompt message builder.

SOLID Principles:
- Single Responsibility: ONLY builds open-ended date/time preference prompt
- Open/Closed: Extensible via subclassing if needed
- Dependency Inversion: Implements MessageBuilder Protocol
"""

from workflows.shared.state import BookingState


class DatePreferencePromptBuilder:
    """Build open-ended prompt asking when customer wants to book.

    Implements MessageBuilder Protocol for use with send_message.node().

    Usage:
        await send_message.node(state, DatePreferencePromptBuilder())
    """

    def __call__(self, state: BookingState) -> str:
        """Build date/time preference prompt from state.

        Args:
            state: Current booking state with customer and service data

        Returns:
            Open-ended prompt asking when to book

        Example:
            state = {
                "customer": {"first_name": "Rahul"},
                "selected_service": {"product_name": "Premium Car Wash"}
            }
            builder = DatePreferencePromptBuilder()
            message = builder(state)
        """
        # Get customer and service data
        customer = state.get("customer", {})
        first_name = customer.get("first_name", "")

        selected_service = state.get("selected_service", {})
        service_name = selected_service.get("product_name", "service")

        # Build personalized prompt
        greeting = f"Great choice, {first_name}!" if first_name else "Great choice!"

        message = f"{greeting}\n\n"
        message += f"When would you like to schedule your *{service_name}*?\n\n"
        message += "You can say things like:\n"
        message += "- 'Tomorrow morning'\n"
        message += "- 'Next Monday afternoon'\n"
        message += "- 'This weekend evening'\n\n"
        message += "Or just tell me what works for you!"

        return message
