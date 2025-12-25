"""Frappe customer lookup request builder.

SOLID Principles:
- Single Responsibility: ONLY builds customer lookup requests
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements RequestBuilder Protocol
"""

from typing import Dict, Any
from workflows.shared.state import BookingState
from core.config import settings
from models.customer import Phone
from models.core import ExtractionMetadata


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
            state = {"conversation_id": "+919876543210"}
            builder = FrappeCustomerLookup()
            request = builder(state)
            # Returns POST request with normalized phone: "9876543210"
        """
        # Get phone number from conversation_id and validate using Phone model
        # Phone model automatically normalizes: +919876543210 → 9876543210
        raw_phone = state.get("conversation_id", "")

        # Use Phone model for validation and normalization
        phone_model = Phone(
            phone_number=raw_phone,
            metadata=ExtractionMetadata(
                confidence=1.0,
                extraction_method="direct",
                extraction_source="wapi_webhook"
            )
        )

        # Phone model validator already removed country code
        phone_normalized = phone_model.phone_number

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
                "filters": {"mobile_no": phone_normalized},
                "fieldname": ["name", "customer_uuid", "enabled", "first_name", "last_name"]
            }
        }
