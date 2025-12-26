"""Atomic fallback extraction node - works with ANY regex pattern configuration.

This single node replaces time_range_fallback.py, date_fallback.py, etc.
Configuration over duplication - follows DRY and SOLID principles.

Usage:
    # Extract time range
    fallback_extract.node(state, TIME_RANGE_PATTERNS, "preferred_time_range", time_extractor)

    # Extract date (SAME node, different config!)
    fallback_extract.node(state, DATE_PATTERNS, "preferred_date", date_extractor)
"""

import logging
from typing import List, Callable, Optional, Any, Dict
from workflows.shared.state import BookingState
from utils.field_utils import set_nested_field

logger = logging.getLogger(__name__)

# Import extractor functions (separated for file size limit compliance)
from fallbacks.pattern_extractors import extract_time_range, extract_date


async def node(
    state: BookingState,
    patterns: List[Any],
    field_path: str,
    extractor_fn: Callable[[str, List[Any]], Optional[Dict[str, Any]]],
    metadata_path: Optional[str] = None
) -> BookingState:
    """Atomic fallback extraction node - works with ANY pattern configuration.

    Args:
        state: Current booking state
        patterns: List of pattern configurations (TimeRangePattern, DatePattern, etc.)
        field_path: Dot-separated path for extracted value
        extractor_fn: Function that performs pattern matching logic
        metadata_path: Optional path to store extraction metadata

    Returns:
        Updated state with extracted data

    Example:
        # Extract time range
        state = await fallback_extract.node(
            state,
            TIME_RANGE_PATTERNS,
            "preferred_time_range",
            extract_time_range
        )

        # Extract date
        state = await fallback_extract.node(
            state,
            DATE_PATTERNS,
            "preferred_date",
            extract_date
        )
    """
    message = state.get("user_message", "")
    if not message:
        logger.warning(f"⚠️ No user message for fallback extraction of {field_path}")
        return state

    try:
        logger.info(f"🔍 Fallback extracting {field_path} using pattern-based extraction")

        # Call the extractor function with message and patterns
        result = extractor_fn(message, patterns)

        if result:
            # Extract the value - result should be a dict
            field_name = field_path.split(".")[-1]
            value = result.get(field_name) or result.get("value")

            if value is not None:
                set_nested_field(state, field_path, value)

                # Store metadata if requested
                if metadata_path:
                    set_nested_field(state, metadata_path, {
                        "extraction_method": "regex",
                        "confidence": result.get("confidence", 0.9)
                    })

                logger.info(f"✅ Fallback extracted {field_path} = {value}")
                return state

        logger.warning(f"⚠️ Fallback extraction returned no value for {field_path}")
        return state

    except Exception as e:
        logger.error(f"❌ Fallback extraction failed for {field_path}: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"fallback_extraction_failed_{field_path}")
        return state
