"""Customer lookup client for chatbot integration.

Provides methods to check customer existence and retrieve customer data.
"""

from typing import Dict, Any
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class CustomerLookupClient:
    """Handle customer lookup and verification operations.

    This client is specifically designed for chatbot integration to verify
    customer existence before processing requests.
    """

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize customer lookup client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def check_customer_exists(self, identifier: str) -> Dict[str, Any]:
        """Check if customer exists by email, phone, or UUID.

        Args:
            identifier: Customer email, phone number, or UUID

        Returns:
            Dict with 'exists' boolean and 'data' dict if found

        Example:
            >>> # Check by email
            >>> result = await client.customer_lookup.check_customer_exists("john@example.com")
            >>> if result["exists"]:
            ...     print(result["data"]["customer_uuid"])
            >>>
            >>> # Check by phone
            >>> result = await client.customer_lookup.check_customer_exists("9876543210")
            >>>
            >>> # Check by UUID
            >>> result = await client.customer_lookup.check_customer_exists("CUST-2025-001")
        """
        # Route to appropriate check method based on identifier format
        if "@" in identifier:
            return await self._check_by_email(identifier)
        elif identifier.startswith("CUST-"):
            return await self._check_by_uuid(identifier)
        else:
            return await self._check_by_phone(identifier)

    async def _check_by_email(self, email: str) -> Dict[str, Any]:
        """Check customer existence by email.

        Args:
            email: Customer email address

        Returns:
            Dict with exists=True/False and data if found
        """
        try:
            result = await self.http.post(
                "/api/method/frappe.client.get_value",
                {
                    "doctype": "User",
                    "filters": {"email": email},
                    "fieldname": ["name", "customer_uuid", "enabled"]
                }
            )
            if result.get("message"):
                return {"exists": True, "data": result["message"]}
            return {"exists": False}

        except NotFoundError:
            logger.debug(f"Customer not found with email: {email}")
            return {"exists": False}

        except FrappeAPIError as e:
            logger.warning(f"API error checking customer by email: {e}")
            return {"exists": False}

    async def _check_by_phone(self, phone: str) -> Dict[str, Any]:
        """Check customer existence by phone number.

        Queries CustomerProfile.phone_number directly - this is where
        all customer data lives (name, UUID, etc).

        Args:
            phone: Customer phone number

        Returns:
            Dict with exists=True/False and data if found
        """
        try:
            result = await self.http.post(
                "/api/method/frappe.client.get_value",
                {
                    "doctype": "CustomerProfile",
                    "filters": {"phone_number": phone},
                    "fieldname": [
                        "customer_uuid",
                        "customer_name",
                        "user",
                        "customer_status"
                    ]
                }
            )
            if result.get("message"):
                cp_data = result["message"]
                # Split customer_name into first/last
                name_parts = (cp_data.get("customer_name") or "").split(" ", 1)
                first_name = name_parts[0] if name_parts else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                logger.info(f"Customer found: {first_name} {last_name}")
                return {
                    "exists": True,
                    "data": {
                        "customer_uuid": cp_data.get("customer_uuid"),
                        "first_name": first_name,
                        "last_name": last_name,
                        "enabled": cp_data.get("customer_status") == "Active",
                        "name": cp_data.get("user")
                    }
                }
            return {"exists": False}

        except NotFoundError:
            logger.debug(f"Customer not found with phone: {phone}")
            return {"exists": False}

        except FrappeAPIError as e:
            logger.warning(f"API error checking customer by phone: {e}")
            return {"exists": False}

    async def _check_by_uuid(self, uuid: str) -> Dict[str, Any]:
        """Check customer existence by UUID.

        Args:
            uuid: Customer UUID (e.g., CUST-2025-001)

        Returns:
            Dict with exists=True/False and data if found
        """
        try:
            result = await self.http.post(
                "/api/method/frappe.client.get",
                {
                    "doctype": "CustomerProfile",
                    "name": uuid
                }
            )
            if result.get("message"):
                return {"exists": True, "data": result["message"]}
            return {"exists": False}

        except NotFoundError:
            logger.debug(f"Customer not found with UUID: {uuid}")
            return {"exists": False}

        except FrappeAPIError as e:
            logger.warning(f"API error checking customer by UUID: {e}")
            return {"exists": False}

    async def get_customer_data(self, uuid: str | None = None) -> Dict[str, Any]:
        """Get complete customer profile data.

        Args:
            uuid: Customer UUID (optional, uses current session user if not provided)

        Returns:
            Customer profile data

        Example:
            >>> # Get current user's profile
            >>> profile = await client.customer_lookup.get_customer_data()
            >>>
            >>> # Get specific customer's profile (admin only)
            >>> profile = await client.customer_lookup.get_customer_data("CUST-2025-001")
        """
        # Note: Original code had uuid parameter but didn't use it
        # The API endpoint returns current user's profile
        # TODO: Add support for admin fetching specific customer profile
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.customer_portal.get_customer_profile"
        )

    async def get_customer_bookings(self, uuid: str | None = None, limit: int = 10) -> Dict[str, Any]:
        """Get customer booking history.

        Args:
            uuid: Customer UUID (optional, uses current session user if not provided)
            limit: Maximum number of bookings to return

        Returns:
            List of customer bookings

        Example:
            >>> bookings = await client.customer_lookup.get_customer_bookings(limit=5)
            >>> for booking in bookings.get("bookings", []):
            ...     print(booking["booking_id"], booking["service_name"])
        """
        # Note: Original code had uuid parameter but didn't use it
        # The API endpoint returns current user's bookings
        # TODO: Add support for admin fetching specific customer bookings
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.booking.get_customer_bookings",
            {"limit": limit}
        )

    async def get_customer_subscriptions(self, uuid: str | None = None) -> Dict[str, Any]:
        """Get customer active subscriptions.

        Args:
            uuid: Customer UUID (optional, uses current session user if not provided)

        Returns:
            Customer subscription data

        Example:
            >>> subs = await client.customer_lookup.get_customer_subscriptions()
            >>> if subs.get("subscription"):
            ...     print(subs["subscription"]["plan_name"])
        """
        # Note: Original code had uuid parameter but didn't use it
        # The API endpoint returns current user's subscription
        # TODO: Add support for admin fetching specific customer subscription
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.customer_portal.get_active_subscription"
        )
