"""Booking creation client for Frappe API.

Handles one-time booking creation and price calculation.

SECURITY: All requests automatically include API key authentication via
Authorization header (configured in .env.txt: FRAPPE_API_KEY, FRAPPE_API_SECRET).
Phone-based methods are secured at the Frappe backend level.
"""

from typing import Dict, Any
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class BookingCreateClient:
    """Handle booking creation operations for one-time services."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize booking create client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new one-time booking.

        Args:
            booking_data: Booking information including:
                - service_id: Service to book
                - vehicle_id: Vehicle for service
                - slot_id: Time slot ID
                - date: Booking date
                - address_id: Service location address
                - optional_addons: List of addon IDs (optional)
                - special_instructions: Customer notes (optional)

        Returns:
            Created booking details with booking ID and payment info

        Example:
            >>> result = await client.booking_create.create_booking({
            ...     "service_id": "SRV-2025-001",
            ...     "vehicle_id": "VEH-2025-001",
            ...     "slot_id": "SLOT-2025-001",
            ...     "date": "2025-01-15",
            ...     "address_id": "ADDR-2025-001",
            ...     "optional_addons": ["ADDON-001", "ADDON-002"],
            ...     "special_instructions": "Please call before arrival"
            ... })
            >>> print(result["booking_id"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.create_booking",
                booking_data
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error creating booking: {e}")
            raise

    async def create_booking_by_phone(
        self,
        phone_number: str,
        booking_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create booking by phone number (no session required).

        This method is designed for WhatsApp bot integration where
        session-based authentication is not available. The Frappe backend
        will lookup the customer by phone and create the booking.

        SECURITY: This request includes API key authentication. The Frappe
        backend validates the API key and should implement rate limiting
        and phone number validation to prevent abuse.

        Args:
            phone_number: Customer phone number (10 digits, no country code)
                         Example: "6290818033" (not "+916290818033")
            booking_data: Booking information including:
                - product_id: Service product ID
                - booking_date: Date for booking (YYYY-MM-DD)
                - slot_id: Time slot ID
                - vehicle_id: Vehicle ID (from get_profile_by_phone vehicles list)
                - address_id: Address ID (from get_profile_by_phone addresses list)
                - electricity_provided: 1 or 0
                - water_provided: 1 or 0
                - addon_ids: List of addon IDs (optional, default: [])
                - payment_mode: "Pay Now" or "Pay Later" (optional)

        Returns:
            Created booking details:
            {
                "success": True,
                "booking_id": "BKG-2025-001",
                "total_amount": 1500.0,
                "message": "Booking created successfully"
            }

        Raises:
            NotFoundError: Customer not found or invalid vehicle/address ID
            FrappeAPIError: API error (e.g., slot unavailable)

        Example:
            >>> # First get profile to get vehicle_id and address_id
            >>> profile = await client.customer_profile.get_profile_by_phone("6290818033")
            >>> vehicle_id = profile["message"]["profile"]["vehicles"][0]["name"]
            >>> address_id = profile["message"]["profile"]["addresses"][0]["name"]
            >>>
            >>> # Then create booking
            >>> result = await client.booking_create.create_booking_by_phone(
            ...     phone_number="6290818033",
            ...     booking_data={
            ...         "product_id": "service-123",
            ...         "booking_date": "2025-01-15",
            ...         "slot_id": "slot-456",
            ...         "vehicle_id": vehicle_id,
            ...         "address_id": address_id,
            ...         "electricity_provided": 1,
            ...         "water_provided": 1,
            ...         "addon_ids": [],
            ...         "payment_mode": "Pay Now"
            ...     }
            ... )
            >>> print(result["message"]["booking_id"])
        """
        try:
            # Add phone number to booking data
            data = {**booking_data, "phone_number": phone_number}

            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.create_booking_by_phone",
                data
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error creating booking by phone {phone_number}: {e}")
            raise

    async def calculate_price(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate booking price before creating booking.

        Args:
            price_data: Price calculation parameters including:
                - product_id: Service product ID (e.g., "suv-premium-one-time")
                - electricity_provided: 1 if available, 0 if not (adds surcharge)
                - water_provided: 1 if available, 0 if not (adds surcharge)
                - addon_ids: List of addon objects (optional)
                  Format: [{"addon": "Engine Bay Cleaning", "quantity": 1, "unit_price": 300.0}, ...]

        Returns:
            Price breakdown including:
                - base_price: Service base price
                - addons_total: Total addon cost
                - water_surcharge: Water surcharge (if water_provided=0)
                - electricity_surcharge: Electricity surcharge (if electricity_provided=0)
                - total_surcharges: Combined surcharges
                - total_amount: Final amount to pay

        Example:
            >>> price = await client.booking_create.calculate_price({
            ...     "product_id": "suv-premium-one-time",
            ...     "electricity_provided": 1,
            ...     "water_provided": 1,
            ...     "addon_ids": [
            ...         {"addon": "Engine Bay Cleaning", "quantity": 1, "unit_price": 300.0}
            ...     ]
            ... })
            >>> print(f"Total: ₹{price['message']['total_amount']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.calculate_booking_price",
                price_data
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error calculating booking price: {e}")
            raise