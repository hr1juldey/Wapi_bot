"""Domain node: Name extraction.

Refactored to use atomic extract.node() - eliminates 82 lines of duplication.
Follows DRY principle: extraction logic lives in atomic layer.
"""

import logging
from typing import Dict, Any, Optional
from workflows.shared.state import BookingState
from nodes.atomic import extract
from dspy_modules.extractors.name_extractor import NameExtractor
from fallbacks.name_fallback import RegexNameExtractor

logger = logging.getLogger(__name__)


def regex_fallback(message: str) -> Dict[str, Any]:
    """Regex fallback for name extraction.

    Uses existing RegexNameExtractor from fallbacks layer.

    Args:
        message: User message

    Returns:
        Dict with first_name and last_name
    """
    extractor = RegexNameExtractor()
    result = extractor.extract(message)

    if result:
        logger.debug(f"Regex extracted name: {result['first_name']}")
        return result

    raise ValueError("Regex name extraction failed")


async def node(
    state: BookingState,
    timeout: Optional[float] = None
) -> BookingState:
    """Extract customer name using atomic extract.node().

    Tier 1: DSPy extraction (via extract.node)
    Tier 2: Regex fallback (via extract.node)
    Tier 3: Graceful degradation (handled by atomic layer)

    Args:
        state: Current booking state
        timeout: Optional extraction timeout

    Returns:
        Updated state with customer.first_name and customer.last_name
    """
    extractor = NameExtractor()

    return await extract.node(
        state,
        extractor,
        field_path="customer",  # Will set customer.first_name, customer.last_name
        fallback_fn=regex_fallback,
        timeout=timeout,
        metadata_path="extraction.name_meta"
    )