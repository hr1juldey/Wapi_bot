"""Domain node: Slot preference extraction.

Extracts date and time preferences using hybrid regex + DSPy approach.
Follows Blender principle: composition over creation.
"""

import logging
import asyncio
from typing import Optional
from workflows.shared.state import BookingState
from dspy_modules.extractors.slot_preference_extractor import SlotPreferenceExtractor
from fallbacks.pattern_extractors import extract_time_range, extract_date
from fallbacks.enhanced_date_fallback import extract_enhanced_date
from models.extraction_patterns import TIME_RANGE_PATTERNS, DATE_PATTERNS
from core.config import settings

logger = logging.getLogger(__name__)


async def node(
    state: BookingState,
    timeout: Optional[float] = None
) -> BookingState:
    """Extract slot preference (time + date) using hybrid regex + DSPy.

    Extraction strategy (regex-first for cost optimization):
    1. Try regex for time range
    2. Try regex for date (basic + enhanced patterns)
    3. Fall back to DSPy for complex inputs

    Args:
        state: Current booking state
        timeout: Optional extraction timeout

    Returns:
        Updated state with preferred_date, preferred_time_range
    """
    message = state.get("user_message", "")
    extraction_timeout = timeout if timeout is not None else settings.extraction_timeout_normal

    # Regex extraction (fast, cheap)
    time_result = extract_time_range(message, TIME_RANGE_PATTERNS)
    date_result = extract_date(message, DATE_PATTERNS)

    # Enhanced date extraction (ordinal, relative dates)
    if not date_result:
        enhanced_result = extract_enhanced_date(message)
        if enhanced_result:
            date_result = enhanced_result
            if enhanced_result.get("needs_confirmation"):
                state["date_confirmation_prompt"] = enhanced_result.get("confirmation_prompt")
                state["needs_date_confirmation"] = True

    # If regex succeeded for at least one field
    if time_result or date_result:
        logger.info("✅ Regex extraction successful for slot preference")
        state["slot_preference_extraction_method"] = "regex"
        if time_result:
            state["preferred_time_range"] = time_result.get("preferred_time_range")
        if date_result:
            state["preferred_date"] = date_result.get("preferred_date")
        return state

    # Fallback to DSPy for complex inputs
    logger.info("⚠️ Regex failed for slot preference, using DSPy")

    try:
        extractor = SlotPreferenceExtractor()
        loop = asyncio.get_event_loop()

        dspy_result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: extractor(
                    conversation_history=state.get("history", []),
                    user_message=message
                )
            ),
            timeout=extraction_timeout
        )

        state["slot_preference_extraction_method"] = "dspy"
        state["preferred_date"] = dspy_result.get("preferred_date", "")
        state["preferred_time_range"] = dspy_result.get("preferred_time_range", "")
        logger.info(f"✅ DSPy extracted slot preference: date={dspy_result.get('preferred_date')}, time={dspy_result.get('preferred_time_range')}")

        return state

    except Exception as e:
        logger.error(f"❌ Slot preference extraction failed: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("extraction_failed_slot_preference")
        return state