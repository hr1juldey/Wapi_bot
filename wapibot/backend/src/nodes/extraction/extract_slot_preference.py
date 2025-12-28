"""Domain node: Slot preference extraction.

Composes atomic extract.node() with SlotPreferenceExtractor.
Follows Blender principle: composition over creation.
"""

import logging
from typing import Dict, Any, Optional
from workflows.shared.state import BookingState
from nodes.atomic import extract
from dspy_modules.extractors.slot_preference_extractor import SlotPreferenceExtractor
from fallbacks.time_range_fallback import RegexTimeRangeExtractor
from fallbacks.date_fallback import RegexDateExtractor

logger = logging.getLogger(__name__)


def regex_fallback(message: str) -> Dict[str, Any]:
    """Regex fallback for slot preference extraction.

    Args:
        message: User message

    Returns:
        Dict with preferred_time and/or preferred_date
    """
    result = {}

    # Try extracting time range
    time_extractor = RegexTimeRangeExtractor()
    time_range = time_extractor.extract(message)
    if time_range:
        result["preferred_time"] = time_range
        logger.debug(f"Regex extracted time: {time_range}")

    # Try extracting date
    date_extractor = RegexDateExtractor()
    date = date_extractor.extract(message)
    if date:
        result["preferred_date"] = date
        logger.debug(f"Regex extracted date: {date}")

    if result:
        return result

    raise ValueError("No slot preference found")


async def node(
    state: BookingState,
    timeout: Optional[float] = None
) -> BookingState:
    """Extract slot preference (time + date) from user message.

    Uses atomic extract.node() with SlotPreferenceExtractor.

    Args:
        state: Current booking state
        timeout: Optional extraction timeout

    Returns:
        Updated state with slot_preference
    """
    extractor = SlotPreferenceExtractor()

    return await extract.node(
        state,
        extractor,
        field_path="slot_preference",
        fallback_fn=regex_fallback,
        timeout=timeout,
        metadata_path="extraction.slot_preference_meta"
    )