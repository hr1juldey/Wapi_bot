"""Frappe services request builder.

SOLID Principles:
- Single Responsibility: ONLY builds service catalog requests
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements RequestBuilder Protocol
"""

from typing import Dict, Any, Optional
from workflows.shared.state import BookingState
from core.config import settings


class FrappeServicesRequest:
    """Build Frappe service catalog HTTP requests.

    Implements RequestBuilder Protocol for use with call_api.node().

    Usage:
        await call_api.node(state, FrappeServicesRequest(), "all_services")
    """

    def __call__(self, state: BookingState) -> Dict[str, Any]:
        """Build service catalog request from state.

        Args:
            state: Current booking state with optional vehicle information

        Returns:
            HTTP request configuration dict

        Example:
            state = {"vehicle": {"vehicle_type": "Hatchback"}}
            builder = FrappeServicesRequest()
            request = builder(state)
            # Returns POST request to get all services (will be filtered later)
        """
        # Build auth headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"token {settings.frappe_api_key}:{settings.frappe_api_secret}"
        }

        # Get vehicle type from state (optional - can filter later with transformer)
        vehicle = state.get("vehicle", {})
        vehicle_type = vehicle.get("vehicle_type")

        # Build request body
        request_body = {
            "category": None,  # Get all categories
            "frequency_type": None,  # Get all frequencies
            "vehicle_type": vehicle_type  # Filter by vehicle type if available
        }

        # Build request
        return {
            "method": "POST",
            "url": f"{settings.frappe_base_url}/api/method/yawlit_automotive_services.api.customer_portal.get_filtered_services",
            "headers": headers,
            "json": request_body
        }
