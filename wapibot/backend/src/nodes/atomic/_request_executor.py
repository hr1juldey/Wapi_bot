"""HTTP request executor with response parsing.

Internal helper for call_api.py - handles HTTP execution details.
"""

import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


async def execute_request(
    client: httpx.AsyncClient,
    request_config: Dict[str, Any],
    timeout: float,
    attempt: int
) -> httpx.Response:
    """Execute a single HTTP request.

    Args:
        client: httpx AsyncClient instance
        request_config: Request configuration dict
        timeout: Request timeout in seconds
        attempt: Current attempt number (for logging)

    Returns:
        httpx Response object

    Raises:
        httpx exceptions on failure
    """
    method = request_config.get("method", "GET")
    url = request_config["url"]
    headers = request_config.get("headers", {})
    params = request_config.get("params", {})
    json_body = request_config.get("json")
    form_data = request_config.get("data")

    logger.info(f"🌐 Attempt {attempt}: {method} {url}")

    response = await client.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=json_body,
        data=form_data,
        timeout=timeout
    )

    response.raise_for_status()
    return response


def default_response_parser(response: httpx.Response) -> Any:
    """Default response parser - returns JSON if available, else text."""
    try:
        return response.json()
    except Exception:
        return response.text


def create_response_metadata(
    response: httpx.Response,
    request_config: Dict[str, Any],
    attempt: int
) -> Dict[str, Any]:
    """Create response metadata dict.

    Args:
        response: httpx Response object
        request_config: Original request configuration
        attempt: Attempt number that succeeded

    Returns:
        Metadata dict
    """
    return {
        "status_code": response.status_code,
        "url": request_config.get("url"),
        "method": request_config.get("method", "GET"),
        "attempt": attempt
    }