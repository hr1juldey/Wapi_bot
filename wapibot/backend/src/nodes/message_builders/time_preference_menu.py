"""Time preference MCQ menu builder.

SOLID Principles:
- Single Responsibility: ONLY builds time-of-day MCQ menu
- Open/Closed: Extensible via subclassing if needed
- Dependency Inversion: Implements MessageBuilder Protocol
"""

from datetime import datetime
from workflows.shared.state import BookingState


class TimePreferenceMenuBuilder:
    """Build MCQ menu for time-of-day selection (morning/afternoon/evening).

    Shown when we have the date but need time preference.
    Implements MessageBuilder Protocol for use with send_message.node().

    Usage:
        await send_message.node(state, TimePreferenceMenuBuilder())
    """

    def __call__(self, state: BookingState) -> str:
        """Build time preference MCQ menu from state.

        Args:
            state: Current booking state with preferred_date

        Returns:
            MCQ menu with time range options

        Example:
            state = {"preferred_date": "2025-12-30"}
            builder = TimePreferenceMenuBuilder()
            message = builder(state)
        """
        # Get preferred date and format it nicely
        preferred_date = state.get("preferred_date", "")
        date_display = self._format_date_display(preferred_date)

        message = f"Got it! For *{date_display}*, which time works best?\n\n"
        message += "1. Morning (8 AM - 12 PM)\n"
        message += "2. Afternoon (12 PM - 5 PM)\n"
        message += "3. Evening (5 PM - 8 PM)\n\n"
        message += "Reply with 1, 2, or 3"

        return message

    def _format_date_display(self, date_str: str) -> str:
        """Format date string for display.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Formatted date like "Monday, Dec 30"
        """
        if not date_str:
            return "your preferred date"

        try:
            date_obj = datetime.fromisoformat(date_str)
            return date_obj.strftime("%A, %b %d")
        except (ValueError, AttributeError):
            return date_str
