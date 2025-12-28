"""Domain node: Yes/No confirmation extraction.

Reusable confirmation node for:
- Booking confirmation
- Addon skip/acceptance
- Utilities selection
- General yes/no questions

Composes atomic extract.node() with regex fallback.
"""

import re
import logging
from typing import Dict, Any
from workflows.shared.state import BookingState
from nodes.atomic import extract

logger = logging.getLogger(__name__)


def regex_fallback(message: str) -> Dict[str, Any]:
    """Regex fallback for yes/no confirmation.

    Patterns:
    - Yes: yes, yeah, yep, sure, ok, confirm, proceed
    - No: no, nope, nah, cancel, skip, decline

    Args:
        message: User message

    Returns:
        Dict with confirmed=True/False
    """
    message_lower = message.lower().strip()

    # Yes patterns
    yes_patterns = r'\b(yes|yeah|yep|yup|sure|ok|okay|confirm|proceed|accept)\b'
    if re.search(yes_patterns, message_lower):
        return {"confirmed": True}

    # No patterns
    no_patterns = r'\b(no|nope|nah|cancel|skip|decline|reject)\b'
    if re.search(no_patterns, message_lower):
        return {"confirmed": False}

    raise ValueError("No clear confirmation found")


# Confirmation extractor Protocol implementation (simple)
class ConfirmationExtractor:
    """Simple confirmation extractor."""

    def __call__(self, conversation_history: list, user_message: str, **kwargs) -> Dict[str, Any]:
        """Extract confirmation from message."""
        # For confirmation, regex is usually sufficient
        # This is a placeholder for LLM-based confirmation if needed
        return regex_fallback(user_message)


async def node(
    state: BookingState,
    field_path: str = "confirmation"
) -> BookingState:
    """Extract yes/no confirmation.

    Args:
        state: Current booking state
        field_path: Where to store result (default: "confirmation")

    Returns:
        Updated state with confirmation
    """
    extractor = ConfirmationExtractor()

    return await extract.node(
        state,
        extractor,
        field_path=field_path,
        fallback_fn=regex_fallback,
        metadata_path=f"extraction.{field_path}_meta"
    )
