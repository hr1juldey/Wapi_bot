"""Atomic extraction node - works with ANY DSPy module.

This single node replaces extract_name.py, extract_phone.py, extract_vehicle.py, etc.
Configuration over specialization - Blender's design principle.

Usage:
    # Extract name
    extract.node(state, NameExtractor(), "customer.first_name", regex_name_fallback)

    # Extract phone (SAME node, different config!)
    extract.node(state, PhoneExtractor(), "customer.phone", regex_phone_fallback)

    # Extract vehicle
    extract.node(state, VehicleExtractor(), "vehicle.brand", None)
"""

import asyncio
import logging
from typing import Any, Callable, Optional, Protocol
from workflows.shared.state import BookingState
from core.config import settings
from utils.field_utils import get_nested_field, set_nested_field

logger = logging.getLogger(__name__)


class Extractor(Protocol):
    """Protocol for DSPy extractors.

    Any DSPy module, ReAct agent, BestOfN, or Refine can be an extractor
    as long as it implements __call__ and returns a dict with extracted data.
    """

    def __call__(
        self,
        conversation_history: list,
        user_message: str,
        **kwargs
    ) -> dict[str, Any]:
        """Extract data from conversation."""
        ...


async def node(
    state: BookingState,
    extractor: Extractor,
    field_path: str,
    fallback_fn: Optional[Callable[[str], dict]] = None,
    timeout: Optional[float] = None,
    metadata_path: Optional[str] = None
) -> BookingState:
    """Atomic extraction node - works with ANY extractor, ANY field.

    This is a workflow-level node (business step), not code-level.
    DSPy modules, ReAct agents, BestOfN, Refine are all extractors (INSIDE this node).

    Args:
        state: Current booking state
        extractor: ANY DSPy module implementing Extractor protocol
        field_path: Dot-separated path for extracted value (e.g., "customer.first_name")
        fallback_fn: Optional fallback function (e.g., regex extractor)
        timeout: Extraction timeout (default: from config)
        metadata_path: Optional path to store extraction metadata

    Returns:
        Updated state with extracted data

    Example:
        # With DSPy ChainOfThought
        extractor = dspy.ChainOfThought(NameExtractionSignature)
        state = await extract.node(state, extractor, "customer.first_name")

        # With BestOfN (runs extractor N times, picks best)
        extractor = BestOfNNameExtractor(n=3)
        state = await extract.node(state, extractor, "customer.first_name")

        # With fallback
        state = await extract.node(
            state,
            NameExtractor(),
            "customer.first_name",
            fallback_fn=regex_name_fallback
        )
    """
    extraction_timeout = timeout if timeout is not None else settings.extraction_timeout_normal

    # Tier 1: Try DSPy extraction
    try:
        logger.info(f"🔍 Extracting {field_path} using {extractor.__class__.__name__}")

        # Run extractor in thread pool (DSPy is sync)
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: extractor(
                    conversation_history=state.get("history", []),
                    user_message=state["user_message"]
                )
            ),
            timeout=extraction_timeout
        )

        # Extract the value - handle both dict and object responses
        if isinstance(result, dict):
            # DSPy returns dict: {"first_name": "Hrijul", "confidence": 0.9}
            # We need to know which field to extract
            field_name = field_path.split(".")[-1]
            value = result.get(field_name) or result.get("value")
            confidence = result.get("confidence", 1.0)
        else:
            # DSPy Prediction object: result.first_name, result.confidence
            field_name = field_path.split(".")[-1]
            value = getattr(result, field_name, None) or getattr(result, "value", None)
            confidence = getattr(result, "confidence", 1.0)

        # Set the extracted value
        if value is not None:
            set_nested_field(state, field_path, value)

            # Store metadata if requested
            if metadata_path:
                set_nested_field(state, metadata_path, {
                    "extraction_method": "dspy",
                    "extractor": extractor.__class__.__name__,
                    "confidence": confidence
                })

            logger.info(f"✅ Extracted {field_path} = {value} (confidence: {confidence})")
            return state
        else:
            raise ValueError(f"Extractor returned no value for {field_path}")

    except (TimeoutError, ConnectionError) as e:
        logger.warning(f"Tier 1 (DSPy) timeout for {field_path}: {e}")

        # Tier 2: Try fallback if provided
        if fallback_fn:
            try:
                logger.info(f"🔄 Trying fallback for {field_path}")
                fallback_result = fallback_fn(state["user_message"])

                if fallback_result:
                    # Fallback returns dict with value and possibly other fields
                    field_name = field_path.split(".")[-1]
                    value = fallback_result.get(field_name) or fallback_result.get("value")

                    if value is not None:
                        set_nested_field(state, field_path, value)

                        if metadata_path:
                            set_nested_field(state, metadata_path, {
                                "extraction_method": "fallback",
                                "confidence": fallback_result.get("confidence", settings.confidence_medium)
                            })

                        logger.info(f"✅ Fallback extracted {field_path} = {value}")
                        return state

                raise ValueError("Fallback returned no value")

            except Exception as fallback_error:
                logger.warning(f"Tier 2 (Fallback) failed for {field_path}: {fallback_error}")

        # Both tiers failed - log error in state
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"extraction_failed_{field_path}")
        logger.error(f"❌ All extraction tiers failed for {field_path}")
        return state

    except Exception as e:
        logger.error(f"DSPy extraction failed for {field_path}: {e}")

        # Try fallback
        if fallback_fn:
            try:
                fallback_result = fallback_fn(state["user_message"])
                field_name = field_path.split(".")[-1]
                value = fallback_result.get(field_name) or fallback_result.get("value")

                if value is not None:
                    set_nested_field(state, field_path, value)

                    if metadata_path:
                        set_nested_field(state, metadata_path, {
                            "extraction_method": "fallback",
                            "confidence": fallback_result.get("confidence", settings.confidence_medium)
                        })

                    logger.info(f"✅ Fallback extracted {field_path} = {value}")
                    return state

            except Exception as fallback_error:
                logger.warning(f"Fallback failed for {field_path}: {fallback_error}")

        # All failed
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"extraction_failed_{field_path}")
        return state
