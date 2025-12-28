"""Domain node for booking price calculation via Frappe API.

SOLID Principles:
- Single Responsibility: ONLY calculates booking price
- Dependency Inversion: Uses call_frappe node (atomic)

DRY Principle:
- Centralizes price calculation logic
- Used by booking_group instead of inline implementation

Blender Architecture:
- Domain node composes atomic nodes (call_frappe)
- Handles one business concern: price calculation
"""

import logging
from workflows.shared.state import BookingState
from nodes.atomic.call_frappe import node as call_frappe_node
from clients.frappe_yawlit import get_yawlit_client

logger = logging.getLogger(__name__)


async def node(state: BookingState) -> BookingState:
    """Calculate booking price using Frappe API.

    Handles addons, utilities, discounts, and taxes.

    Args:
        state: Must contain:
            - selected_service: Service with base_price
            - addon_ids: List of addon objects
            - electricity_provided: 0 or 1
            - water_provided: 0 or 1

    Returns:
        Updated state with:
            - total_price: Final calculated price
            - price_breakdown: API response with breakdown

    Fallback:
        If API fails, uses service base_price as total_price
    """
    selected_service = state.get("selected_service", {})
    base_price = selected_service.get("base_price", 0)

    try:
        client = get_yawlit_client()

        def extract_price_params(s):
            addon_ids = s.get("addon_ids", [])

            # CRITICAL: Use SAME format as create_booking_by_phone
            price_params = {
                "price_data": {
                    "product_id": selected_service.get("name"),
                    "addon_ids": addon_ids,
                    "electricity_provided": s.get("electricity_provided", 1),
                    "water_provided": s.get("water_provided", 1)
                }
            }

            addon_names = [a.get("addon") for a in addon_ids] if addon_ids else []
            logger.info(f"💰 Price params: product={selected_service.get('name')}, "
                       f"addons={addon_names}, elec={s.get('electricity_provided', 1)}, "
                       f"water={s.get('water_provided', 1)}")
            return price_params

        logger.info("💰 Calling calculate_booking_price API...")
        result = await call_frappe_node(
            state,
            client.booking_create.calculate_price,
            "price_breakdown",
            state_extractor=extract_price_params
        )

        # Extract total_price from API response
        price_api_response = result.get("price_breakdown", {})
        price_breakdown = price_api_response.get("message", {})
        total_price = price_breakdown.get("total_amount")

        if total_price and total_price > 0:
            result["total_price"] = total_price
            addon_amount = (price_breakdown.get('addon_price', 0) or
                          price_breakdown.get('addons_total', 0))
            logger.info(f"💰 API price: ₹{total_price} "
                       f"(base: {price_breakdown.get('base_price', 0)}, "
                       f"addons: {addon_amount}, tax: {price_breakdown.get('tax', 0)})")
            logger.info(f"💰 Full price breakdown: {price_breakdown}")
            return result
        else:
            raise ValueError("Invalid price from API")

    except Exception as e:
        # Fallback to base price
        logger.warning(f"💰 Price calculation failed: {e}. Using base_price: ₹{base_price}")
        state["total_price"] = base_price
        state["price_breakdown"] = {
            "base_price": base_price,
            "addon_price": 0,
            "discount": 0,
            "tax": 0,
            "total_price": base_price
        }
        return state
