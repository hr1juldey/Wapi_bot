"""Utilities selection message builder.

Extracted from utilities_group.py - asks about electricity and water availability.

Implements MessageBuilder Protocol for use with send_message.node().
"""

from workflows.shared.state import BookingState


class UtilitiesSelectionBuilder:
    """Build utilities availability question message.

    Asks customer about electricity and water availability at service location.
    """

    def __call__(self, state: BookingState) -> str:
        """Build utilities question message from state.

        Args:
            state: Current booking state with customer info

        Returns:
            Formatted utilities question message
        """
        customer_name = state.get("customer", {}).get("first_name", "there")

        return f"""Hi {customer_name}! 👋

To complete your booking, we need to know about utilities at your service location:

1. *Electricity* ⚡ - Do you have electricity available?
2. *Water* 💧 - Do you have a water connection?

Please reply with:
• *"Yes Yes"* - if both are available
• *"Yes No"* - if only electricity is available
• *"No Yes"* - if only water is available
• *"No No"* - if neither is available

Example: "Yes Yes"
"""