"""FastAPI middleware initialization.

Centralizes security, CORS, rate limiting, and activity tracking middleware.
"""

import logging
import hashlib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.security_config import security_settings
from core.warmup import warmup_service
from security.secret_manager import secret_manager
from middlewares.auth.auth_middleware import AuthMiddleware
from middlewares.auth.jwt_validator import JWTValidator
from middlewares.auth.api_key_validator import APIKeyValidator
from middlewares.rate_limit.rate_limit_middleware import RateLimitMiddleware

logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Security Headers Middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers (production only)."""
        response = await call_next(request)
        if security_settings.is_production:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
            response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Server"] = "WapiBot"
        return response

    # Rate Limiting
    app.add_middleware(RateLimitMiddleware)

    # Authentication
    try:
        admin_key = secret_manager.decrypt_value(security_settings.api_key_admin or "")
        brain_key = secret_manager.decrypt_value(security_settings.api_key_brain or "")

        validators = [
            JWTValidator(secret_key=security_settings.jwt_secret_key or "dev_secret"),
            APIKeyValidator(valid_keys={
                hashlib.sha256(admin_key.encode()).hexdigest(): {
                    "name": "admin_key",
                    "scopes": ["admin", "payments", "brain"]
                },
                hashlib.sha256(brain_key.encode()).hexdigest(): {
                    "name": "brain_key",
                    "scopes": ["brain"]
                }
            } if admin_key and brain_key else {})
        ]

        app.add_middleware(AuthMiddleware, validators=validators)
        logger.info(f"🔐 Security initialized ({security_settings.environment})")
    except Exception as e:
        logger.warning(f"⚠️  Security initialization skipped: {e}")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Accept", "Authorization", "X-API-Key"],
    )

    # Activity tracking
    @app.middleware("http")
    async def track_activity(request: Request, call_next):
        """Track API activity for idle warmup monitoring."""
        warmup_service.update_activity()
        response = await call_next(request)
        return response
