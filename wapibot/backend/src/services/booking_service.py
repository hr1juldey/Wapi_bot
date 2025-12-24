"""Booking service for Yawlit API integration.

Handles creating bookings via Yawlit API.
"""

import httpx
from typing import Dict, Any

from models.booking_state import BookingState
from core.config import settings


class BookingService:
    """Service for creating bookings via Yawlit API."""

    def __init__(self):
        """Initialize booking service."""
        self.api_base_url = settings.yawlit_api_url
        self.api_key = settings.yawlit_api_key

    async def create_booking(self, state: BookingState) -> Dict[str, Any]:
        """Create booking via Yawlit API.

        Args:
            state: Complete booking state

        Returns:
            API response with booking_id or error
        """
        if not state:
            return {
                "success": False,
                "error": "Invalid booking state"
            }

        # Build API payload
        payload = self._build_payload(state)

        # Call Yawlit API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/bookings",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )

                if response.status_code == 201:
                    return {
                        "success": True,
                        "booking_id": response.json().get("id"),
                        "data": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }

    def _build_payload(self, state: BookingState) -> Dict[str, Any]:
        """Build API payload from booking state.

        Args:
            state: Booking state

        Returns:
            API payload dict
        """
        return {
            "customer": {
                "first_name": state.get("customer", {}).get("first_name"),
                "last_name": state.get("customer", {}).get("last_name"),
                "phone": state.get("customer", {}).get("phone_number"),
                "email": state.get("customer", {}).get("email")
            },
            "vehicle": {
                "brand": state.get("vehicle", {}).get("brand"),
                "model": state.get("vehicle", {}).get("model"),
                "year": state.get("vehicle", {}).get("year")
            },
            "appointment": {
                "date": state.get("appointment", {}).get("date", {}).get("parsed_date"),
                "time_slot_id": state.get("appointment", {}).get("time_slot_id"),
                "service_type": state.get("appointment", {}).get("service_type")
            }
        }


# Singleton instance
booking_service = BookingService()
