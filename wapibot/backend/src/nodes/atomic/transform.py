"""Atomic transform node - works with ANY transformer.

SOLID Principles:
- Single Responsibility: ONLY transforms data
- Open/Closed: Extensible via Transformer protocol
- Dependency Inversion: Depends on Protocol, not concrete class

DRY Principle:
- ONE implementation for ALL transformations (filter, format, calculate)
- Uses centralized field_utils (no duplication)

Brain Integration:
- Observes transformation patterns for learning
- Brain can optimize transformation strategies in conscious mode
"""

import logging
from typing import Any, Protocol
from workflows.shared.state import BookingState
from utils.field_utils import get_nested_field, set_nested_field
from core.brain_config import get_brain_settings

logger = logging.getLogger(__name__)


class Transformer(Protocol):
    """Protocol for transformer functions (Dependency Inversion).

    Transformers take data and state context, return transformed data.
    This enables:
    - Filters (lambda data, s: [x for x in data if condition])
    - Formatters (lambda data, s: format_as_string(data))
    - Calculators (lambda data, s: calculate_metrics(data))
    - Enrichers (lambda data, s: {**data, 'extra': value})
    """

    def __call__(self, data: Any, state: BookingState) -> Any:
        """Transform data with state context.

        Args:
            data: Source data to transform
            state: Full state for context-aware transformations

        Returns:
            Transformed data
        """
        ...


async def node(
    state: BookingState,
    transformer: Transformer,
    source_path: str,
    target_path: str,
    on_empty: str = "skip"
) -> BookingState:
    """Transform data from source to target using ANY transformer.

    Single Responsibility: ONLY transforms data (doesn't extract, validate, send messages)

    Uses field_utils for nested field access (DRY - implemented once, used everywhere).

    Args:
        state: Current booking state
        transformer: ANY function implementing Transformer protocol
        source_path: Dot notation path to source data (e.g., "all_services")
        target_path: Dot notation path to store result (e.g., "filtered_services")
        on_empty: Action when source is empty - "skip", "raise", or "default"

    Returns:
        Updated state with transformed data at target_path

    Examples:
        # Filter services by vehicle type
        await transform.node(state, filter_by_vehicle, "all_services", "filtered")

        # Calculate completeness percentage
        await transform.node(state, calc_completeness, "customer", "completeness")

        # Format catalog for display
        await transform.node(state, format_catalog, "services", "formatted_catalog")
    """
    # Get source data using field_utils (DRY)
    source_data = get_nested_field(state, source_path)

    if source_data is None:
        logger.warning(f"⚠️ Source path '{source_path}' is empty")

        if on_empty == "raise":
            raise ValueError(f"Source path '{source_path}' is empty")
        elif on_empty == "skip":
            return state  # No transformation, continue workflow
        elif on_empty == "default":
            set_nested_field(state, target_path, None)
            return state

    # Transform data
    try:
        # Brain observation: track transformation patterns
        brain_settings = get_brain_settings()
        if brain_settings.brain_enabled:
            logger.debug(f"🧠 Brain observing transformation: {source_path}→{target_path} (mode: {brain_settings.brain_mode})")
            # TODO: In Phase 4, brain will learn which transformations are most effective
            # e.g., "FilterSlots with morning preference → 80% booking success rate"

        transformed_data = transformer(source_data, state)
        logger.info(f"🔄 Transformed {source_path} → {target_path}")

        # Store result using field_utils (DRY)
        set_nested_field(state, target_path, transformed_data)

        # Brain feedback: successful transformation
        if brain_settings.brain_enabled:
            logger.debug(f"🧠 Transformation successful: {transformer.__class__.__name__}")

        return state

    except Exception as e:
        logger.error(f"❌ Transformation failed for {target_path}: {e}")

        # Brain observation: track transformation failures for learning
        brain_settings = get_brain_settings()
        if brain_settings.brain_enabled:
            logger.debug(f"🧠 Brain observing transformation failure: {source_path}→{target_path}")
            # TODO: Brain can suggest alternative transformation strategies

        # Log error in state
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"transform_error_{target_path}")

        # Re-raise if requested
        if on_empty == "raise":
            raise

        return state
