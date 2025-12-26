"""Date preference MCQ menu builder.

SOLID Principles:
- Single Responsibility: ONLY builds date selection MCQ menu
- Open/Closed: Extensible via subclassing if needed
- Dependency Inversion: Implements MessageBuilder Protocol
"""

from datetime import datetime, timedelta
from workflows.shared.state import BookingState


class DatePreferenceMenuBuilder:
    """Build MCQ menu for date selection (today/tomorrow/specific dates).

    Shown when we have the time range but need date preference.
    Implements MessageBuilder Protocol for use with send_message.node().

    Usage:
        await send_message.node(state, DatePreferenceMenuBuilder())
    """

    def __call__(self, state: BookingState) -> str:
        """Build date preference MCQ menu from state.

        Args:
            state: Current booking state with preferred_time_range

        Returns:
            MCQ menu with date options

        Example:
            state = {"preferred_time_range": "morning"}
            builder = DatePreferenceMenuBuilder()
            message = builder(state)
        """
        # Get preferred time range
        time_range = state.get("preferred_time_range", "")
        time_display = time_range if time_range else "your preferred time"

        # Generate date options
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)

        message = f"Perfect for the {time_display}! Which day works for you?\n\n"
        message += f"1. Today ({today.strftime('%A, %b %d')})\n"
        message += f"2. Tomorrow ({tomorrow.strftime('%A, %b %d')})\n"
        message += f"3. {day_after.strftime('%A, %b %d')}\n"
        message += "4. Next week\n\n"
        message += "Reply with 1, 2, 3, or 4"

        return message
