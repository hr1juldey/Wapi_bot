"""Resume/reset prompt message builder.

Asks user if they want to resume previous booking or start fresh.
"""

from workflows.shared.state import BookingState


class ResumePromptBuilder:
    """Build resume/reset choice message.

    Implements MessageBuilder Protocol for use with send_message.node().
    """

    def __call__(self, state: BookingState) -> str:
        """Build resume/reset prompt.

        Args:
            state: Current booking state (may have partial data)

        Returns:
            Choice prompt message
        """
        # Check what partial data exists
        has_customer = bool(state.get("customer"))
        has_vehicle = bool(state.get("vehicle"))
        has_service = bool(state.get("selected_service"))

        message = "👋 Welcome back!\n\n"

        if has_customer or has_vehicle or has_service:
            message += "I see you have an incomplete booking.\n\n"
            message += "Would you like to:\n"
            message += "1️⃣ *RESUME* - Continue where you left off\n"
            message += "2️⃣ *RESET* - Start a new booking\n\n"
            message += "Reply with *1* or *2*"
        else:
            message += "Let's get started with your booking!"
            state["should_proceed"] = True  # No choice needed, proceed

        return message
