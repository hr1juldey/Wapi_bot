"""Frappe customer lookup request builder.

SOLID Principles:
- Single Responsibility: ONLY builds customer lookup requests
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements RequestBuilder Protocol
"""

from typing import Dict, Any
from workflows.shared.state import BookingState
from core.config import settings


class FrappeCustomerLookup:
    """Build Frappe customer lookup HTTP requests.

    Implements RequestBuilder Protocol for use with call_api.node().

    Usage:
        await call_api.node(state, FrappeCustomerLookup(), "customer_data")
    """

    def __call__(self, state: BookingState) -> Dict[str, Any]:
        """Build customer lookup request from state.

        Args:
            state: Current booking state with conversation_id (phone number)

        Returns:
            HTTP request configuration dict

        Example:
            state = {"conversation_id": "919876543210"}
            builder = FrappeCustomerLookup()
            request = builder(state)
            # Returns POST request to check customer existence by phone
        """
        # Get phone number from conversation_id (format: 919876543210)
        phone = state.get("conversation_id", "")

        # Build auth headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"token {settings.frappe_api_key}:{settings.frappe_api_secret}"
        }

        # Build request (uses frappe.client.get_value to check User by phone)
        return {
            "method": "POST",
            "url": f"{settings.frappe_base_url}/api/method/frappe.client.get_value",
            "headers": headers,
            "json": {
                "doctype": "User",
                "filters": {"mobile_no": phone},
                "fieldname": ["name", "customer_uuid", "enabled", "first_name", "last_name"]
            }
        }
