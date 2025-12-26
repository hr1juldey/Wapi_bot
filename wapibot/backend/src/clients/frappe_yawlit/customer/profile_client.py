"""Customer profile client for Frappe API.

Handles customer profile operations including profile management and vehicle management.

SECURITY: All requests automatically include API key authentication via
Authorization header (configured in .env.txt: FRAPPE_API_KEY, FRAPPE_API_SECRET).
Phone-based methods are secured at the Frappe backend level.
"""

from typing import Dict, Any
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class CustomerProfileClient:
    """Handle customer profile and vehicle management operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize customer profile client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_profile(self) -> Dict[str, Any]:
        """Get customer profile (requires session).

        Returns:
            Customer profile data including personal details and preferences

        Example:
            >>> profile = await client.customer_profile.get_profile()
            >>> print(profile["customer_name"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.get_customer_profile"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching customer profile: {e}")
            raise

    async def get_profile_by_phone(self, phone_number: str) -> Dict[str, Any]:
        """Get customer profile by phone number (no session required).

        This method is designed for WhatsApp bot integration where
        session-based authentication is not available. The Frappe backend
        will lookup the customer by phone and return their profile.

        SECURITY: This request includes API key authentication. The Frappe
        backend validates the API key and should implement rate limiting
        and phone number validation to prevent abuse.

        Args:
            phone_number: Customer phone number (10 digits, no country code)
                         Example: "6290818033" (not "+916290818033")

        Returns:
            Customer profile data in Frappe response format:
            {
                "message": {
                    "success": True,
                    "profile": {
                        "customer_uuid": "LIT-CUST-...",
                        "full_name": "John Doe",
                        "email": "john@example.com",
                        "mobile_no": "9876543210",
                        "address": "123 Main St",
                        "city": "Bangalore",
                        "state": "Karnataka",
                        "pincode": "560001",
                        "customer_tier": "Bronze",
                        "vehicles": [...],
                        "addresses": [...],
                        "needs_email": False,
                        "pending_email_verification": False
                    }
                }
            }

        Raises:
            NotFoundError: Customer not found
            FrappeAPIError: API error (e.g., incomplete profile)

        Example:
            >>> profile = await client.customer_profile.get_profile_by_phone("6290818033")
            >>> profile_data = profile["message"]["profile"]
            >>> print(profile_data["full_name"])
            >>> print(f"Vehicles: {len(profile_data['vehicles'])}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.get_profile_by_phone",
                {"phone_number": phone_number}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching customer profile by phone {phone_number}: {e}")
            raise

    async def complete_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete customer profile after registration.

        Args:
            data: Profile data including:
                - customer_name: Full name
                - email: Email address
                - phone_number: Phone number
                - default_address: Default address
                - city: City
                - state: State
                - pincode: PIN code
                - Additional optional fields

        Returns:
            Profile completion confirmation

        Example:
            >>> result = await client.customer_profile.complete_profile({
            ...     "customer_name": "John Doe",
            ...     "email": "john@example.com",
            ...     "phone_number": "9876543210",
            ...     "default_address": "123 Main St",
            ...     "city": "Bangalore",
            ...     "state": "Karnataka",
            ...     "pincode": "560001"
            ... })
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.complete_profile",
                {"data": data}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error completing profile: {e}")
            raise

    async def update_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer profile.

        Args:
            data: Profile fields to update (same structure as complete_profile)

        Returns:
            Update confirmation

        Example:
            >>> result = await client.customer_profile.update_profile({
            ...     "customer_name": "John Smith",
            ...     "phone_number": "9876543211"
            ... })
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.update_profile",
                {"data": data}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error updating profile: {e}")
            raise

    async def get_vehicles(self) -> Dict[str, Any]:
        """Get customer vehicles.

        Returns:
            List of customer's registered vehicles

        Example:
            >>> vehicles = await client.customer_profile.get_vehicles()
            >>> for vehicle in vehicles.get("vehicles", []):
            ...     print(vehicle["vehicle_number"], vehicle["vehicle_make"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.get_customer_vehicles"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching vehicles: {e}")
            raise

    async def add_vehicle(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add vehicle to customer profile.

        Args:
            vehicle_data: Vehicle information including:
                - vehicle_make: Manufacturer (e.g., Honda, Toyota)
                - vehicle_model: Model name
                - vehicle_number: Registration number
                - vehicle_type: Type (e.g., Sedan, SUV)
                - Additional optional fields

        Returns:
            Added vehicle details

        Example:
            >>> result = await client.customer_profile.add_vehicle({
            ...     "vehicle_make": "Honda",
            ...     "vehicle_model": "City",
            ...     "vehicle_number": "KA01AB1234",
            ...     "vehicle_type": "Sedan"
            ... })
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.add_vehicle",
                {"vehicle_data": vehicle_data}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error adding vehicle: {e}")
            raise

    async def update_vehicle(self, vehicle_name: str, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update vehicle information.

        Args:
            vehicle_name: Vehicle document name/ID
            vehicle_data: Vehicle fields to update

        Returns:
            Update confirmation

        Example:
            >>> result = await client.customer_profile.update_vehicle(
            ...     "VEH-2025-001",
            ...     {"vehicle_number": "KA01AB5678"}
            ... )
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.update_vehicle",
                {
                    "vehicle_name": vehicle_name,
                    "vehicle_data": vehicle_data
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error updating vehicle {vehicle_name}: {e}")
            raise

    async def delete_vehicle(self, vehicle_name: str) -> Dict[str, Any]:
        """Delete vehicle from customer profile.

        Args:
            vehicle_name: Vehicle document name/ID to delete

        Returns:
            Deletion confirmation

        Example:
            >>> result = await client.customer_profile.delete_vehicle("VEH-2025-001")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.delete_vehicle",
                {"vehicle_name": vehicle_name}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error deleting vehicle {vehicle_name}: {e}")
            raise