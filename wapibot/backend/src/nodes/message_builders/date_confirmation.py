"""Date confirmation message builder.

Used when date extraction has ambiguity and needs user confirmation.
Example: User says "31st" → "Did you mean December 31st?"
"""

from workflows.shared.state import BookingState


class DateConfirmationBuilder:
    """Build date confirmation message.

    Implements MessageBuilder Protocol for use with send_message.node().
    """

    def __call__(self, state: BookingState) -> str:
        """Build confirmation message from state.

        Args:
            state: Current booking state with date extraction results

        Returns:
            Confirmation question for user
        """
        # Get the confirmation prompt from date extraction
        confirmation_prompt = state.get("date_confirmation_prompt", "")

        if confirmation_prompt:
            return f"📅 {confirmation_prompt}\n\nPlease reply *YES* or *NO*."

        # Fallback if no specific prompt
        preferred_date = state.get("preferred_date", "")
        if preferred_date:
            return f"📅 Did you mean {preferred_date}?\n\nPlease reply *YES* or *NO*."

        # Last resort fallback
        return "📅 Please confirm the date you want to book.\n\nReply with the date in format: DD/MM/YYYY"