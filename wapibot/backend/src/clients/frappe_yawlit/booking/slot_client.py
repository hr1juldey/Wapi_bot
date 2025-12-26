"""Slot availability client for Frappe API.

Handles time slot discovery, availability checking, and calendar views.
"""

from typing import Dict, Any, Optional
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class SlotAvailabilityClient:
    """Handle slot availability and booking time management."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize slot availability client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_available_slots_enhanced(
        self,
        service_id: str,
        date: str,
        vehicle_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get enhanced available slots for a specific date.

        Args:
            service_id: Service ID to check slots for
            date: Date in YYYY-MM-DD format
            vehicle_type: Vehicle type filter (optional)

        Returns:
            Enhanced slot information including:
                - slots: List of available time slots
                - slot_id: Slot identifier
                - start_time: Slot start time
                - end_time: Slot end time
                - available_capacity: Number of bookings available
                - total_capacity: Maximum bookings
                - price: Slot-specific pricing (if applicable)

        Example:
            >>> slots = await client.slot_availability.get_available_slots_enhanced(
            ...     "SRV-2025-001",
            ...     "2025-01-15",
            ...     "Sedan"
            ... )
            >>> for slot in slots["slots"]:
            ...     print(f"{slot['start_time']}-{slot['end_time']}: {slot['available_capacity']} available")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.get_available_slots_enhanced",
                {
                    "service_id": service_id,
                    "date_str": date,  # Frappe endpoint expects "date_str" parameter
                    "vehicle_type": vehicle_type
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching available slots for {service_id} on {date}: {e}")
            raise

    async def get_calendar_availability(
        self,
        service_id: str,
        month: str,
        year: str
    ) -> Dict[str, Any]:
        """Get calendar availability overview for entire month.

        Args:
            service_id: Service ID to check availability
            month: Month number (1-12)
            year: Year (YYYY)

        Returns:
            Calendar view with availability for each day:
                - dates: Dict with date as key and availability info as value
                - has_slots: Boolean for each date
                - available_count: Number of available slots
                - is_fully_booked: Boolean if all slots taken
                - is_holiday: Boolean if business closed

        Example:
            >>> calendar = await client.slot_availability.get_calendar_availability(
            ...     "SRV-2025-001",
            ...     "1",
            ...     "2025"
            ... )
            >>> for date, info in calendar["dates"].items():
            ...     if info["has_slots"]:
            ...         print(f"{date}: {info['available_count']} slots")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.get_calendar_availability_enhanced",
                {
                    "service_id": service_id,
                    "month": month,
                    "year": year
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching calendar availability for {service_id}: {e}")
            raise

    async def check_slot_availability(self, slot_id: str) -> Dict[str, Any]:
        """Check real-time availability for a specific slot.

        Args:
            slot_id: Slot ID to check

        Returns:
            Slot availability status:
                - is_available: Boolean indicating availability
                - available_capacity: Current capacity
                - total_capacity: Maximum capacity
                - slot_info: Slot details (time, date, service)
                - warning: Any warnings about the slot (optional)

        Example:
            >>> status = await client.slot_availability.check_slot_availability("SLOT-2025-001")
            >>> if status["is_available"]:
            ...     print(f"Slot available: {status['available_capacity']} spots left")
            >>> else:
            ...     print("Slot is fully booked")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.check_slot_availability",
                {"slot_id": slot_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error checking slot availability for {slot_id}: {e}")
            raise
