"""Authentication validator protocols.

Protocol-based design for DRY authentication (SOLID principles).
"""

from typing import Protocol, Optional, Dict, Any
from fastapi import Request


class AuthValidator(Protocol):
    """Protocol for authentication validators.

    Follows same pattern as WAPI webhook signature validation.
    Allows ANY validator implementation (JWT, API Key, HMAC, OAuth2).
    """

    async def validate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate request authentication.

        Args:
            request: FastAPI request object

        Returns:
            User context dict if valid: {"user_id": str, "scopes": List[str]}
            None if invalid or no auth present
        """
        ...

    def get_auth_scheme(self) -> str:
        """Return auth scheme name for logging.

        Returns:
            Scheme name (e.g., "Bearer", "APIKey", "HMAC")
        """
        ...