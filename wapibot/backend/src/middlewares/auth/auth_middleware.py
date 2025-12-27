"""Main authentication middleware.

Protocol-based, environment-aware authentication dispatcher.
"""

import logging
from typing import List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from middlewares.auth.protocols import AuthValidator
from security.endpoint_registry import get_endpoint_security_config
from core.security_config import security_settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware accepting ANY validator (DRY/SOLID)."""

    def __init__(self, app, validators: List[AuthValidator]):
        """Initialize auth middleware.

        Args:
            app: FastAPI app instance
            validators: List of auth validators (JWT, API Key, etc.)
        """
        super().__init__(app)
        self.validators = validators

    async def dispatch(self, request: Request, call_next):
        """Dispatch request with authentication check.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response from handler or 401/403 error
        """
        path = request.url.path

        # Skip auth in development (unless forced)
        if security_settings.is_development:
            config = get_endpoint_security_config(path)
            if not config.get("force_auth_in_dev", False):
                logger.debug(f"[DEV MODE] Skipping auth: {path}")
                return await call_next(request)

        # Get endpoint security requirements
        config = get_endpoint_security_config(path)
        if not config.get("requires_auth"):
            return await call_next(request)

        # Try each validator
        user_context = None
        for validator in self.validators:
            user_context = await validator.validate(request)
            if user_context:
                logger.info(
                    f"Authenticated via {user_context.get('auth_method')}: "
                    f"{user_context.get('user_id')}"
                )
                break

        # No valid auth found
        if not user_context:
            logger.warning(f"Unauthorized access attempt: {path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )

        # Check scopes (authorization)
        required_scopes = config.get("required_scopes", [])
        if required_scopes:
            user_scopes = set(user_context.get("scopes", []))
            if not set(required_scopes).issubset(user_scopes):
                logger.warning(
                    f"Insufficient permissions for {user_context.get('user_id')}: "
                    f"required={required_scopes}, has={list(user_scopes)}"
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Insufficient permissions"}
                )

        # Attach user context to request
        request.state.user = user_context

        return await call_next(request)
