"""Frappe create booking request builder.

SOLID Principles:
- Single Responsibility: ONLY builds booking creation requests
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements RequestBuilder Protocol
"""

from typing import Dict, Any
from workflows.shared.state import BookingState
from core.config import settings


class FrappeCreateBookingRequest:
    """Build Frappe booking creation HTTP requests.

    Implements RequestBuilder Protocol for use with call_api.node().

    Usage:
        await call_api.node(state, FrappeCreateBookingRequest(), "booking_response")
    """

    def __call__(self, state: BookingState) -> Dict[str, Any]:
        """Build booking creation request from state.

        Args:
            state: Current booking state with customer, vehicle, service, appointment

        Returns:
            HTTP request configuration dict

        Example:
            state = {
                "customer": {"customer_uuid": "CUST-2025-001"},
                "vehicle": {"vehicle_id": "VEH-2025-001"},
                "selected_service": {"service_id": "SRV-2025-001"},
                "appointment": {"date": "2025-12-25", "slot_id": "SLOT-2025-001"},
                "address_id": "ADDR-2025-001"
            }
        """
        # Build auth headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"token {settings.frappe_api_key}:{settings.frappe_api_secret}"
        }

        # Extract booking data from state
        customer = state.get("customer", {})
        vehicle = state.get("vehicle", {})
        service = state.get("selected_service", {})
        appointment = state.get("appointment", {})

        # Build booking request body
        booking_data = {
            "customer_uuid": customer.get("customer_uuid"),
            "service_id": service.get("service_id"),
            "vehicle_id": vehicle.get("vehicle_id"),
            "slot_id": appointment.get("slot_id"),
            "date": appointment.get("date"),
            "address_id": state.get("address_id"),
            "optional_addons": state.get("optional_addons", []),
            "special_instructions": state.get("special_instructions", "")
        }

        # Build request
        return {
            "method": "POST",
            "url": f"{settings.frappe_base_url}/api/method/yawlit_automotive_services.api.booking.create_booking",
            "headers": headers,
            "json": booking_data
        }
