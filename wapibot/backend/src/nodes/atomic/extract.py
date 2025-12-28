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
from typing import Any, Callable, Optional, Protocol, Literal
from workflows.shared.state import BookingState
from core.config import settings
from core.brain_config import get_brain_settings
from utils.field_utils import set_nested_field

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
    metadata_path: Optional[str] = None,
    extraction_priority: Optional[Literal["regex_first", "dspy_first"]] = None
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
        extraction_priority: Order to try methods ("regex_first" or "dspy_first")
                           Defaults to brain_mode setting (reflex=regex, conscious=dspy)

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

        # Brain-controlled priority
        state = await extract.node(
            state,
            extractor,
            "customer.first_name",
            fallback_fn=regex_fallback,
            extraction_priority="regex_first"  # Brain sets this based on mode
        )
    """
    extraction_timeout = timeout if timeout is not None else settings.extraction_timeout_normal

    # Determine extraction priority (brain-controlled configuration)
    if extraction_priority is None:
        brain_settings = get_brain_settings()
        extraction_priority = "regex_first" if brain_settings.brain_mode == "reflex" else "dspy_first"

    # Determine method order based on priority
    method_order = ["regex", "dspy"] if extraction_priority == "regex_first" else ["dspy", "regex"]

    field_name = field_path.split(".")[-1]

    # Try methods in priority order
    for method_name in method_order:
        try:
            # Skip regex if no fallback function provided
            if method_name == "regex" and not fallback_fn:
                continue

            if method_name == "dspy":
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

                # Extract value - handle both dict and object responses
                if isinstance(result, dict):
                    value = result.get(field_name) or result.get("value")
                    confidence = result.get("confidence", 1.0)
                else:
                    value = getattr(result, field_name, None) or getattr(result, "value", None)
                    confidence = getattr(result, "confidence", 1.0)

            else:  # method_name == "regex"
                logger.info(f"🔄 Trying regex fallback for {field_path}")
                result = fallback_fn(state["user_message"])

                if not result:
                    raise ValueError("Fallback returned no result")

                value = result.get(field_name) or result.get("value")
                confidence = result.get("confidence", settings.confidence_medium)

            # Store extracted value if found
            if value is None:
                raise ValueError(f"No value extracted from {method_name}")

            set_nested_field(state, field_path, value)

            # Store metadata if requested
            if metadata_path:
                set_nested_field(state, metadata_path, {
                    "extraction_method": method_name,
                    "extractor": extractor.__class__.__name__ if method_name == "dspy" else "regex",
                    "confidence": confidence
                })

            logger.info(f"✅ Extracted {field_path} = {value} via {method_name} (confidence: {confidence})")
            return state

        except Exception as e:
            logger.warning(f"{method_name} extraction failed for {field_path}: {e}")
            continue  # Try next method

    # All methods failed
    if "errors" not in state:
        state["errors"] = []
    state["errors"].append(f"extraction_failed_{field_path}")
    logger.error(f"❌ All extraction methods failed for {field_path}")
    return state
