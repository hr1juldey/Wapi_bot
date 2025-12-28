"""Decorator for automatic brain observation on atomic nodes.

Simplifies brain observation by wrapping atomic node calls:

Usage:
    # Without hook (manual observation):
    state = await extract.node(state, extractor, "customer.name")
    state = await observe_brain.node(state, "extraction.brain_obs", {...})

    # With hook (automatic observation):
    @observe_brain_hook("extraction.brain_obs")
    async def extract_name(state):
        return await extract.node(state, extractor, "customer.name")

    state = await extract_name(state)  # Observation happens automatically
"""

import logging
import time
from functools import wraps
from typing import Callable, Optional, Dict, Any
from workflows.shared.state import BookingState
from nodes.atomic import observe_brain
from core.brain_config import get_brain_settings

logger = logging.getLogger(__name__)


def observe_brain_hook(
    observation_path: str,
    include_timing: bool = True,
    include_mode: bool = True,
    custom_metadata: Optional[Dict[str, Any]] = None
):
    """Decorator that automatically observes brain decisions before/after node execution.

    Args:
        observation_path: Where to store observation (e.g., "extraction.brain_obs")
        include_timing: Record execution time
        include_mode: Record brain mode
        custom_metadata: Additional metadata to record

    Returns:
        Decorator function

    Example:
        @observe_brain_hook("validation.brain_obs")
        async def validate_customer(state):
            return await validate.node(state, CustomerModel, "customer")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(state: BookingState, *args, **kwargs) -> BookingState:
            brain_settings = get_brain_settings()

            # Skip observation if brain disabled
            if not brain_settings.brain_enabled:
                return await func(state, *args, **kwargs)

            # Prepare observation data
            observation_data: Dict[str, Any] = {}

            if include_mode:
                observation_data["brain_mode"] = brain_settings.brain_mode

            if custom_metadata:
                observation_data.update(custom_metadata)

            # Record function name
            observation_data["function"] = func.__name__

            # Execute node with timing
            start_time = time.time()
            result_state = await func(state, *args, **kwargs)
            execution_time = time.time() - start_time

            if include_timing:
                observation_data["execution_time_ms"] = round(execution_time * 1000, 2)

            # Record observation
            result_state = await observe_brain.node(
                result_state,
                observation_path,
                observation_data
            )

            logger.debug(
                f"📊 Brain observation: {observation_path} "
                f"[{brain_settings.brain_mode}] {execution_time*1000:.1f}ms"
            )

            return result_state

        return wrapper

    return decorator