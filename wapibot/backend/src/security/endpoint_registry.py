"""Central endpoint security configuration.

Single source of truth for auth requirements, scopes, and rate limits.
"""

import re
from typing import Dict, Any


# Endpoint security configuration
ENDPOINT_SECURITY_CONFIG = {
    # Admin Endpoints - CRITICAL (currently unprotected)
    "/admin/payments/confirm": {
        "requires_auth": True,
        "required_scopes": ["admin", "payments"],
        "rate_limit": 2,
        "force_auth_in_dev": True,  # Always require auth (even in dev)
    },
    "/admin/payments/status/.*": {  # Regex pattern
        "requires_auth": True,
        "required_scopes": ["admin"],
        "rate_limit": 5,
        "force_auth_in_dev": True,
    },

    # Brain Endpoints - DoS Risk
    "/brain/dream": {
        "requires_auth": True,
        "required_scopes": ["brain", "admin"],
        "rate_limit": 1,  # Expensive operation
    },
    "/brain/train": {
        "requires_auth": True,
        "required_scopes": ["brain"],
        "rate_limit": 1,
    },
    "/brain/status": {
        "requires_auth": True,
        "required_scopes": ["brain", "admin"],
        "rate_limit": 5,
    },
    "/brain/features": {
        "requires_auth": True,
        "required_scopes": ["brain", "admin"],
        "rate_limit": 5,
    },
    "/brain/decisions": {
        "requires_auth": True,
        "required_scopes": ["brain", "admin"],
        "rate_limit": 5,
    },

    # QR Endpoint - Enumeration Risk
    "/api/v1/qr/.*": {
        "requires_auth": False,  # Public (WAPI needs access)
        "rate_limit": 8,
        "force_rate_limit_in_dev": True,  # Always rate limit
    },

    # Chat Endpoint - Public but rate limited
    "/api/v1/chat": {
        "requires_auth": False,
        "rate_limit": 5,
    },

    # WAPI Webhook - Has HMAC validation in endpoint
    "/api/v1/wapi/webhook": {
        "requires_auth": True,  # HMAC handled in endpoint
        "rate_limit": 10,
        "force_auth_in_dev": False,
    },
}


def get_endpoint_security_config(path: str) -> Dict[str, Any]:
    """Get security config for endpoint.

    Supports both exact matches and regex patterns.

    Args:
        path: Request path (e.g., "/admin/payments/confirm")

    Returns:
        Security config dict with keys: requires_auth, required_scopes, rate_limit
    """
    # Exact match first
    if path in ENDPOINT_SECURITY_CONFIG:
        return ENDPOINT_SECURITY_CONFIG[path]

    # Regex patterns
    for pattern, config in ENDPOINT_SECURITY_CONFIG.items():
        if re.match(pattern, path):
            return config

    # Default: no auth, standard rate limit
    return {"requires_auth": False, "rate_limit": 10}
