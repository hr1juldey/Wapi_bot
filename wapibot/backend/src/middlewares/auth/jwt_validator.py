"""JWT Bearer token validator.

Validates Authorization: Bearer <token> headers using PyJWT.
"""

import jwt
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class JWTValidator:
    """JWT Bearer token validator implementing AuthValidator protocol."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        verify_exp: bool = True
    ):
        """Initialize JWT validator.

        Args:
            secret_key: Secret key for JWT signature verification
            algorithm: JWT algorithm (default: HS256)
            verify_exp: Verify expiration (default: True)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.verify_exp = verify_exp

    async def validate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate JWT from Authorization header.

        Args:
            request: FastAPI request object

        Returns:
            User context if valid, None if invalid
        """
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        # Check Bearer scheme
        if not auth_header.startswith("Bearer "):
            return None

        # Extract token
        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": self.verify_exp}
            )

            # Extract user context
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "scopes": payload.get("scopes", []),
                "auth_method": "jwt"
            }

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    def get_auth_scheme(self) -> str:
        """Return auth scheme name."""
        return "Bearer"

    def generate_token(
        self,
        user_id: str,
        email: str,
        scopes: list,
        expiration_minutes: int = 60
    ) -> str:
        """Generate JWT token (for testing/user creation).

        Args:
            user_id: User ID
            email: User email
            scopes: List of scopes
            expiration_minutes: Token expiration time

        Returns:
            Encoded JWT token
        """
        payload = {
            "sub": user_id,
            "email": email,
            "scopes": scopes,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=expiration_minutes)
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
