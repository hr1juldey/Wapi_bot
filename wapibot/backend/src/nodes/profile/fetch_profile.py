"""Profile fetching node using unified get_profile_by_phone API.

Replaces old 3-node chain:
- lookup_customer → check_customer_exists
- check_profile_complete → get_profile
- fetch_vehicles → get_vehicles

Now: ONE node, ONE API call.
"""

import logging
from typing import Dict, Any
from workflows.shared.state import BookingState
from clients.frappe_yawlit import get_yawlit_client
from models.customer import Phone
from models.core import ExtractionMetadata

logger = logging.getLogger(__name__)


async def fetch_complete_profile(state: BookingState) -> BookingState:
    """Fetch customer profile + vehicles + addresses in one call.

    Inputs:
    - state["conversation_id"]: Phone number from webhook

    Outputs:
    - state["customer"]: Customer details + UUID
    - state["vehicle"]: Auto-selected vehicle (if only 1)
    - state["vehicle_options"]: Vehicle list (if multiple)
    - state["addresses"]: Address list for booking
    - state["profile_complete"]: Validation flag
    """
    client = get_yawlit_client()

    # Normalize phone number
    raw_phone = state.get("conversation_id", "")
    phone_model = Phone(
        phone_number=raw_phone,
        metadata=ExtractionMetadata(
            confidence=1.0,
            extraction_method="direct",
            extraction_source="wapi_webhook"
        )
    )
    normalized_phone = phone_model.phone_number

    logger.info(f"📞 Fetching complete profile for: {raw_phone} → {normalized_phone}")

    try:
        # ONE API call replaces 3
        response = await client.customer_profile.get_profile_by_phone(normalized_phone)

        # Check if customer exists
        if not response.get("message", {}).get("success"):
            logger.warning("⚠️ Customer not found")
            state["customer"] = None
            state["profile_complete"] = False
            state["vehicle_selected"] = False
            state["vehicle_options"] = []
            return state

        # Extract profile data
        profile = response["message"]["profile"]
        logger.info(f"✅ Profile loaded: {profile.get('full_name')}")

        # Populate customer bundle
        state["customer"] = {
            "customer_uuid": profile.get("customer_uuid"),
            "first_name": profile.get("full_name", "").split()[0] if profile.get("full_name") else "",
            "last_name": " ".join(profile.get("full_name", "").split()[1:]) if profile.get("full_name") and len(profile.get("full_name", "").split()) > 1 else "",
            "phone": profile.get("mobile_no"),
            "email": profile.get("email"),
            "customer_status": "Active",
            "confidence": 1.0
        }

        # Validate profile completeness
        required_fields = ["customer_uuid", "full_name", "email", "mobile_no", "city", "state", "pincode"]
        missing_fields = [f for f in required_fields if not profile.get(f)]
        state["profile_complete"] = len(missing_fields) == 0

        # Debug: Log what we found
        logger.info(f"🔍 Profile fields check: {[(f, profile.get(f)) for f in required_fields]}")
        logger.info(f"🔍 Missing fields: {missing_fields}")
        logger.info(f"🔍 Profile complete: {state['profile_complete']}")

        if missing_fields:
            state["missing_profile_fields"] = missing_fields
            logger.warning(f"⚠️ Profile incomplete - missing: {missing_fields}")
        else:
            logger.info("✅ Profile is complete")

        # Process vehicles
        vehicles = profile.get("vehicles", [])
        logger.info(f"🚗 Found {len(vehicles)} vehicle(s)")

        if len(vehicles) == 1:
            # Auto-select single vehicle
            v = vehicles[0]
            state["vehicle"] = {
                "vehicle_id": v.get("name"),
                "vehicle_number": v.get("vehicle_number"),
                "vehicle_make": v.get("vehicle_make"),
                "vehicle_model": v.get("vehicle_model"),
                "vehicle_type": v.get("vehicle_type"),
                "is_primary": v.get("is_primary", 1)
            }
            state["vehicle_selected"] = True
            logger.info(f"✅ Auto-selected vehicle: {v.get('vehicle_number')}")
        elif len(vehicles) > 1:
            # Multiple vehicles - show options
            state["vehicle"] = None
            state["vehicle_options"] = [
                {
                    "vehicle_id": v.get("name"),
                    "vehicle_number": v.get("vehicle_number"),
                    "vehicle_make": v.get("vehicle_make"),
                    "vehicle_model": v.get("vehicle_model"),
                    "vehicle_type": v.get("vehicle_type"),
                    "is_primary": v.get("is_primary", 0)
                }
                for v in vehicles
            ]
            state["vehicle_selected"] = False
            logger.info(f"Multiple vehicles - user selects from {len(vehicles)} options")
        else:
            # No vehicles
            state["vehicle"] = None
            state["vehicle_options"] = []
            state["vehicle_selected"] = False
            logger.info("No vehicles - user needs to add one")

        # Store addresses for booking
        state["addresses"] = profile.get("addresses", [])

        return state

    except Exception as e:
        logger.error(f"❌ Error fetching profile: {e}", exc_info=True)
        state["customer"] = None
        state["profile_complete"] = False
        state["profile_error"] = str(e)
        state["vehicle_selected"] = False
        state["vehicle_options"] = []
        return state
