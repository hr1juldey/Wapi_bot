"""Retry handler with brain-aware strategies.

Internal helper for call_api.py - handles retry logic and error handling.
"""

import logging
from typing import Any, Callable, Dict, Optional

import httpx

from ._request_executor import execute_request, create_response_metadata

logger = logging.getLogger(__name__)


async def execute_with_retry(
    request_config: Dict[str, Any],
    response_parser: Callable[[httpx.Response], Any],
    retry_count: int,
    timeout: float
) -> tuple[Optional[Any], Optional[Dict[str, Any]], Optional[Exception]]:
    """Execute HTTP request with retry logic.

    Args:
        request_config: Request configuration dict
        response_parser: Function to parse response
        retry_count: Number of retry attempts
        timeout: Request timeout in seconds

    Returns:
        Tuple of (parsed_data, metadata, error)
        - parsed_data: Parsed response data (None if failed)
        - metadata: Response metadata dict (None if failed)
        - error: Exception if failed (None if success)
    """
    last_error = None

    async with httpx.AsyncClient() as client:
        for attempt in range(1, retry_count + 1):
            try:
                # Execute request
                response = await execute_request(
                    client, request_config, timeout, attempt
                )

                # Parse response
                try:
                    parsed_data = response_parser(response)
                    metadata = create_response_metadata(response, request_config, attempt)

                    logger.info(f"✅ API call successful: {request_config.get('url')}")
                    return (parsed_data, metadata, None)

                except Exception as parse_error:
                    logger.error(f"❌ Response parsing failed: {parse_error}")
                    return (None, None, parse_error)  # Don't retry parse errors

            except httpx.HTTPStatusError as e:
                logger.warning(f"⚠️ HTTP error (attempt {attempt}/{retry_count}): {e.response.status_code}")
                last_error = e

                # Don't retry on 4xx client errors
                if 400 <= e.response.status_code < 500:
                    break

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(f"⚠️ Network error (attempt {attempt}/{retry_count}): {type(e).__name__}")
                last_error = e

            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                last_error = e
                break

    # All retries exhausted
    return (None, None, last_error)