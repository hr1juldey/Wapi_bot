"""Domain node: Utilities (electricity/water) extraction.

Extracts yes/no for electricity and water availability.
Composes atomic extract.node() with regex fallback.
"""

import re
import logging
from typing import Dict, Any
from workflows.shared.state import BookingState
from nodes.atomic import extract

logger = logging.getLogger(__name__)


def electricity_regex_fallback(message: str) -> Dict[str, Any]:
    """Regex fallback for electricity availability.

    Args:
        message: User message

    Returns:
        Dict with electricity=True/False
    """
    message_lower = message.lower().strip()

    # Positive patterns
    if re.search(r'\b(yes|have|available|there is)\b.*\belect', message_lower):
        return {"electricity": True}

    # Negative patterns
    if re.search(r'\b(no|don\'t have|not available|no elect)', message_lower):
        return {"electricity": False}

    raise ValueError("Could not determine electricity availability")


def water_regex_fallback(message: str) -> Dict[str, Any]:
    """Regex fallback for water availability.

    Args:
        message: User message

    Returns:
        Dict with water=True/False
    """
    message_lower = message.lower().strip()

    # Positive patterns
    if re.search(r'\b(yes|have|available|there is)\b.*\bwater', message_lower):
        return {"water": True}

    # Negative patterns
    if re.search(r'\b(no|don\'t have|not available|no water)', message_lower):
        return {"water": False}

    raise ValueError("Could not determine water availability")


# Simple extractor Protocol implementations
class ElectricityExtractor:
    """Electricity availability extractor."""

    def __call__(self, conversation_history: list, user_message: str, **kwargs) -> Dict[str, Any]:
        return electricity_regex_fallback(user_message)


class WaterExtractor:
    """Water availability extractor."""

    def __call__(self, conversation_history: list, user_message: str, **kwargs) -> Dict[str, Any]:
        return water_regex_fallback(user_message)


async def extract_electricity(state: BookingState) -> BookingState:
    """Extract electricity availability."""
    return await extract.node(
        state,
        ElectricityExtractor(),
        field_path="utilities.electricity",
        fallback_fn=electricity_regex_fallback
    )


async def extract_water(state: BookingState) -> BookingState:
    """Extract water availability."""
    return await extract.node(
        state,
        WaterExtractor(),
        field_path="utilities.water",
        fallback_fn=water_regex_fallback
    )