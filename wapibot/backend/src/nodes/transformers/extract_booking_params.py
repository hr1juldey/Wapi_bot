"""Transformer for extracting booking creation parameters from state.

SOLID Principles:
- Single Responsibility: ONLY extracts booking params
- Open/Closed: Implements Transformer protocol

DRY Principle:
- Centralizes booking params extraction logic
- Eliminates inline extraction in booking_group

Blender Architecture:
- Transformer: data → data (no side effects)
- Used by transform.node() atomic node
"""

import logging
from typing import Dict, Any
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)


class ExtractBookingParams:
    """Transformer that extracts booking parameters for Frappe API."""

    def __call__(self, _data: Any, state: BookingState) -> Dict[str, Any]:
        """Extract booking params from state.

        Args:
            _data: Ignored (state is the source)
            state: Booking state with all required fields

        Returns:
            Dict with phone_number and booking_data for create_booking_by_phone API

        Raises:
            ValueError: If required fields are missing
        """
        customer = state.get("customer", {})
        selected_service = state.get("selected_service", {})
        slot = state.get("slot", {})

        # Extract and normalize phone from conversation_id
        phone = state.get("conversation_id", "")
        if phone.startswith("91") and len(phone) == 12:
            phone = phone[2:]  # Remove country code
        elif len(phone) == 10:
            phone = phone  # Already correct
        else:
            logger.warning(f"Unexpected phone format: {phone}")
            phone = phone[-10:]  # Fallback: last 10 digits

        logger.info(f"📱 Phone normalized: {state.get('conversation_id')} → {phone}")

        # Extract booking data fields
        product_id = selected_service.get("name")
        booking_date = slot.get("date")
        slot_id = slot.get("name")
        vehicle_id = state.get("vehicle", {}).get("vehicle_id")
        address_id = state.get("selected_address_id") or customer.get("default_address_id")

        # Validate required fields
        missing_fields = []
        if not product_id:
            missing_fields.append("product_id")
        if not booking_date:
            missing_fields.append("booking_date")
        if not slot_id:
            missing_fields.append("slot_id")
        if not vehicle_id:
            missing_fields.append("vehicle_id")
        if not address_id:
            missing_fields.append("address_id")

        if missing_fields:
            logger.error(f"❌ Missing required fields: {', '.join(missing_fields)}")
            logger.error(f"   selected_service keys: {list(selected_service.keys())}")
            logger.error(f"   slot keys: {list(slot.keys())}")
            logger.error(f"   vehicle keys: {list(state.get('vehicle', {}).keys())}")
            logger.error(f"   customer keys: {list(customer.keys())}")
            raise ValueError(f"Missing required booking fields: {', '.join(missing_fields)}")

        # Log booking data
        addon_ids = state.get("addon_ids", [])
        logger.info(f"📋 Booking data: product_id={product_id}, date={booking_date}, "
                   f"slot_id={slot_id}, vehicle_id={vehicle_id}, address_id={address_id}, "
                   f"addon_ids={addon_ids}")

        # Return phone_number and booking_data (API signature)
        return {
            "phone_number": phone,
            "booking_data": {
                "product_id": product_id,
                "booking_date": booking_date,
                "slot_id": slot_id,
                "vehicle_id": vehicle_id,
                "address_id": address_id,
                "electricity_provided": state.get("electricity_provided", 1),
                "water_provided": state.get("water_provided", 1),
                "addon_ids": state.get("addon_ids", []),
                "payment_mode": "Pay Now"
            }
        }
