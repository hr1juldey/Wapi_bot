"""API Key validator.

Validates X-API-Key header using constant-time comparison.
"""

import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
from fastapi import Request

logger = logging.getLogger(__name__)


class APIKeyValidator:
    """API Key validator implementing AuthValidator protocol."""

    def __init__(self, valid_keys: Dict[str, Dict[str, Any]]):
        """Initialize API key validator.

        Args:
            valid_keys: Dict mapping hashed keys to metadata
                Example: {
                    "sha256_of_key": {
                        "name": "admin_key",
                        "scopes": ["admin", "payments"]
                    }
                }
        """
        self.valid_keys = valid_keys

    async def validate(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate API key from X-API-Key header.

        Args:
            request: FastAPI request object

        Returns:
            User context if valid, None if invalid
        """
        # Get X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return None

        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Check if key exists (constant-time comparison)
        for valid_hash, metadata in self.valid_keys.items():
            if hmac.compare_digest(key_hash, valid_hash):
                logger.info(f"Valid API key: {metadata.get('name')}")
                return {
                    "user_id": metadata.get("name"),
                    "scopes": metadata.get("scopes", []),
                    "auth_method": "api_key"
                }

        logger.warning("Invalid API key provided")
        return None

    def get_auth_scheme(self) -> str:
        """Return auth scheme name."""
        return "APIKey"

    @staticmethod
    def hash_key(plaintext_key: str) -> str:
        """Hash an API key for storage.

        Args:
            plaintext_key: Plaintext API key

        Returns:
            SHA-256 hash of key
        """
        return hashlib.sha256(plaintext_key.encode()).hexdigest()