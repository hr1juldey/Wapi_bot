"""Rate limiting middleware.

Environment-aware rate limiting using sliding window algorithm.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from middlewares.rate_limit.sliding_window import rate_limiter
from security.endpoint_registry import get_endpoint_security_config
from core.security_config import security_settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with sliding window algorithm."""

    async def dispatch(self, request: Request, call_next):
        """Dispatch request with rate limit check.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response from handler or 429 Too Many Requests
        """
        # Skip if rate limiting disabled
        if not security_settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path

        # Skip in dev mode (unless forced)
        if security_settings.is_development:
            config = get_endpoint_security_config(path)
            if not config.get("force_rate_limit_in_dev", False):
                return await call_next(request)

        # Get endpoint rate limit
        config = get_endpoint_security_config(path)
        limit = config.get("rate_limit", 10)

        # Generate key: IP + path
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{path}"

        # Check rate limit
        allowed = await rate_limiter.check_limit(key, limit, 1)

        if not allowed:
            logger.warning(f"Rate limit exceeded: {key} (limit: {limit}/s)")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": limit,
                    "window": "1 second"
                },
                headers={"Retry-After": "1"}
            )

        # Get remaining requests
        remaining = await rate_limiter.get_remaining(key, limit, 1)

        # Continue with request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = "1"

        return response
