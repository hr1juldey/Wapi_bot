"""Atomic API call node - works with ANY HTTP API.

Generic, configurable HTTP client. NOT specific to Yawlit, Frappe, or any API.
Configuration over specialization - pass request builder functions.

Usage:
    # Call Yawlit API
    call_api.node(state, yawlit_request_builder, "customer_api_response")

    # Call Frappe API (SAME node, different config!)
    call_api.node(state, frappe_request_builder, "booking_api_response")

    # Call weather API
    call_api.node(state, weather_request_builder, "weather_data")
"""

import logging
from typing import Any, Dict, Optional, Protocol, Literal

import httpx

from workflows.shared.state import BookingState
from core.brain_config import get_brain_settings
from utils.field_utils import set_nested_field
from ._request_executor import default_response_parser
from ._retry_handler import execute_with_retry

logger = logging.getLogger(__name__)


class RequestBuilder(Protocol):
    """Protocol for request builder functions."""

    def __call__(self, state: BookingState) -> Dict[str, Any]:
        """Build HTTP request from state."""
        ...


class ResponseParser(Protocol):
    """Protocol for response parser functions."""

    def __call__(self, response: httpx.Response) -> Any:
        """Parse HTTP response."""
        ...


async def node(
    state: BookingState,
    request_builder: RequestBuilder,
    result_path: str,
    response_parser: Optional[ResponseParser] = None,
    retry_count: Optional[int] = None,
    timeout: Optional[float] = None,
    on_failure: Literal["log", "raise", "clear"] = "log"
) -> BookingState:
    """Atomic API call node - works with ANY HTTP API.

    Args:
        state: Current booking state
        request_builder: Function that builds HTTP request from state
        result_path: Where to store the result in state
        response_parser: Optional function to parse response (default: JSON parser)
        retry_count: Number of retries (default: from brain settings)
        timeout: Request timeout in seconds (default: from brain settings)
        on_failure: Action on failure - "log", "raise", "clear"
    """
    # Brain-aware defaults
    brain_settings = get_brain_settings()
    if retry_count is None:
        retry_count = 1 if brain_settings.brain_mode == "reflex" else 3
    if timeout is None:
        timeout = 5.0 if brain_settings.brain_mode == "reflex" else 10.0
    if response_parser is None:
        response_parser = default_response_parser

    # Build request
    try:
        request_config = request_builder(state)
    except Exception as e:
        logger.error(f"❌ Request builder failed: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"api_request_builder_error_{result_path}")
        if on_failure == "raise":
            raise
        return state

    # Execute with retry
    parsed_data, metadata, error = await execute_with_retry(
        request_config, response_parser, retry_count, timeout
    )

    # Handle result
    if error is None:
        # Success
        set_nested_field(state, result_path, parsed_data)
        set_nested_field(state, f"{result_path}_metadata", metadata)
        return state

    # Failure
    logger.error(f"❌ API call failed after {retry_count} attempts: {error}")
    if "errors" not in state:
        state["errors"] = []
    state["errors"].append(f"api_call_failed_{result_path}")

    if on_failure == "raise":
        raise error
    elif on_failure == "clear":
        set_nested_field(state, result_path, None)

    return state