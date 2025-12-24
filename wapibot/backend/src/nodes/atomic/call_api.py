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

    # Any HTTP API!
"""

import logging
import httpx
from typing import Any, Callable, Dict, Optional, Protocol
from workflows.shared.state import BookingState
from utils.field_utils import get_nested_field, set_nested_field

logger = logging.getLogger(__name__)


class RequestBuilder(Protocol):
    """Protocol for request builder functions.

    Request builders create HTTP request configurations from state.
    They are NOT tied to any specific API.
    """

    def __call__(self, state: BookingState) -> Dict[str, Any]:
        """Build HTTP request from state.

        Returns:
            Dict with:
                - method: "GET", "POST", "PUT", "DELETE", etc.
                - url: Full URL
                - headers: Optional dict of headers
                - params: Optional query parameters
                - json: Optional JSON body
                - data: Optional form data
        """
        ...


class ResponseParser(Protocol):
    """Protocol for response parser functions.

    Response parsers extract data from HTTP responses.
    They are NOT tied to any specific API.
    """

    def __call__(self, response: httpx.Response) -> Any:
        """Parse HTTP response.

        Args:
            response: httpx Response object

        Returns:
            Parsed data (dict, list, str, etc.)
        """
        ...


def default_response_parser(response: httpx.Response) -> Any:
    """Default response parser - returns JSON if available, else text."""
    try:
        return response.json()
    except Exception:
        return response.text


async def node(
    state: BookingState,
    request_builder: RequestBuilder,
    result_path: str,
    response_parser: Optional[ResponseParser] = None,
    retry_count: int = 3,
    timeout: float = 10.0,
    on_failure: str = "log"
) -> BookingState:
    """Atomic API call node - works with ANY HTTP API.

    Completely generic - works with Yawlit, Frappe, weather API, anything!
    Configuration happens through request_builder and response_parser functions.

    Args:
        state: Current booking state
        request_builder: Function that builds HTTP request from state
        result_path: Where to store the result in state (e.g., "api_response")
        response_parser: Optional function to parse response (default: JSON parser)
        retry_count: Number of retries on failure (default: 3)
        timeout: Request timeout in seconds (default: 10.0)
        on_failure: Action on failure - "log", "raise", "clear" (default: "log")

    Returns:
        Updated state with API response

    Example:
        # Define request builder for Yawlit customer lookup
        def yawlit_customer_lookup(state: BookingState) -> dict:
            phone = state.get("customer", {}).get("phone", "")
            return {
                "method": "GET",
                "url": "https://api.yawlit.com/customers",
                "params": {"phone": phone},
                "headers": {"Authorization": f"Bearer {api_key}"}
            }

        # Define response parser
        def parse_yawlit_customer(response: httpx.Response) -> dict:
            data = response.json()
            return {
                "first_name": data.get("firstName"),
                "last_name": data.get("lastName"),
                "email": data.get("email")
            }

        # Use atomic call_api node
        state = await call_api.node(
            state,
            yawlit_customer_lookup,
            "customer_data",
            parse_yawlit_customer
        )

        # Same node, different API!
        def frappe_create_booking(state: BookingState) -> dict:
            return {
                "method": "POST",
                "url": "https://frappe.example.com/api/resource/Booking",
                "json": {
                    "customer": state.get("customer", {}).get("first_name"),
                    "vehicle": state.get("vehicle", {}).get("brand")
                },
                "headers": {"Authorization": f"token {token}"}
            }

        state = await call_api.node(
            state,
            frappe_create_booking,
            "booking_response"
        )
    """
    # Use default parser if none provided
    if response_parser is None:
        response_parser = default_response_parser

    # Build request from state
    try:
        request_config = request_builder(state)
        logger.info(f"🌐 Calling {request_config.get('method', 'GET')} {request_config.get('url')}")

    except Exception as e:
        logger.error(f"❌ Request builder failed: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"api_request_builder_error_{result_path}")

        if on_failure == "raise":
            raise

        return state

    # Make HTTP request with retries
    last_error = None

    async with httpx.AsyncClient() as client:
        for attempt in range(retry_count):
            try:
                # Extract request parameters
                method = request_config.get("method", "GET")
                url = request_config["url"]
                headers = request_config.get("headers", {})
                params = request_config.get("params", {})
                json_body = request_config.get("json")
                form_data = request_config.get("data")

                # Make request
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    data=form_data,
                    timeout=timeout
                )

                # Check for HTTP errors
                response.raise_for_status()

                # Parse response
                try:
                    parsed_data = response_parser(response)
                    set_nested_field(state, result_path, parsed_data)

                    logger.info(f"✅ API call successful: {url}")

                    # Store metadata
                    metadata_path = f"{result_path}_metadata"
                    set_nested_field(state, metadata_path, {
                        "status_code": response.status_code,
                        "url": url,
                        "method": method,
                        "attempt": attempt + 1
                    })

                    return state

                except Exception as parse_error:
                    logger.error(f"❌ Response parsing failed: {parse_error}")
                    last_error = parse_error
                    break  # Don't retry on parse errors

            except httpx.HTTPStatusError as e:
                logger.warning(f"⚠️ HTTP error (attempt {attempt + 1}/{retry_count}): {e}")
                last_error = e

                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    break

                # Retry on 5xx errors (server errors)
                continue

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"⚠️ Network error (attempt {attempt + 1}/{retry_count}): {e}")
                last_error = e
                continue

            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                last_error = e
                break

    # All retries failed
    logger.error(f"❌ API call failed after {retry_count} attempts: {last_error}")

    if "errors" not in state:
        state["errors"] = []
    state["errors"].append(f"api_call_failed_{result_path}")

    if on_failure == "raise":
        raise last_error

    elif on_failure == "clear":
        set_nested_field(state, result_path, None)

    # Default: "log" - just log and continue
    return state
