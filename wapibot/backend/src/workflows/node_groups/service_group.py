"""Service selection node group.

Handles:
- Fetching service catalog
- Displaying services to user
- Processing service selection
- Error handling

Replaces 6 old nodes:
- fetch_services
- send_service_catalog
- await_service_selection
- process_service_selection
- handle_service_selection_error
- route_service_selection
"""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.selection.generic_handler import handle_selection, route_after_selection
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.call_frappe import node as call_frappe_node
from nodes.message_builders.service_catalog import ServiceCatalogBuilder
from clients.frappe_yawlit import get_yawlit_client

logger = logging.getLogger(__name__)


async def fetch_services(state: BookingState) -> BookingState:
    """Fetch service catalog from Frappe."""
    client = get_yawlit_client()

    result = await call_frappe_node(
        state,
        client.service_catalog.get_filtered_services,
        "services_response",
        state_extractor=lambda s: {
            "vehicle_type": s.get("vehicle", {}).get("vehicle_type")
        } if s.get("vehicle") else {}
    )

    # Extract services from response
    services_response = result.get("services_response", {})
    services = services_response.get("message", {}).get("services", [])

    # Fallbacks for different response structures
    if not services:
        services = services_response.get("services", [])
    if not services:
        services = services_response.get("data", {}).get("services", [])
    if not services and isinstance(services_response.get("message"), list):
        services = services_response["message"]

    logger.info(f"🛠️ Fetched {len(services)} service(s)")
    result["service_options"] = services

    return result


async def show_service_catalog(state: BookingState) -> BookingState:
    """Display service catalog to user, then pause for user input."""
    result = await send_message_node(state, ServiceCatalogBuilder())

    # Pause and wait for user's service selection
    result["should_proceed"] = False
    result["current_step"] = "awaiting_service_selection"
    return result


async def process_service_selection(state: BookingState) -> BookingState:
    """Process service selection from user."""
    result = await handle_selection(
        state,
        selection_type="service",
        options_key="service_options",
        selected_key="selected_service"  # Must match BookingState field name!
    )
    # Clear current_step to indicate we're moving to the next step (slot selection)
    # This allows slot_group to do a fresh fetch with the selected service
    if result.get("selected_service"):
        result["current_step"] = ""
        result["should_proceed"] = True  # Continue to next step
    return result


async def send_service_error(state: BookingState) -> BookingState:
    """Send error message for invalid service selection."""
    error_msg = state.get("selection_error", "Invalid selection. Please try again.")
    result = await send_message_node(state, lambda s: error_msg)
    result["should_proceed"] = False  # Stop and wait for next user message
    result["current_step"] = "awaiting_service_selection"  # Resume here on next message
    return result


def route_service_entry(state: BookingState) -> str:
    """Route based on whether we're resuming or starting fresh."""
    current_step = state.get("current_step", "")
    has_services = bool(state.get("service_options"))

    if current_step == "awaiting_service_selection" and has_services:
        logger.info("🔀 Resuming service selection - skipping fetch")
        return "process_selection"
    else:
        logger.info("🔀 Starting fresh service fetch")
        return "fetch_services"


def create_service_group() -> StateGraph:
    """Create service selection node group."""
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("entry", lambda s: s)  # Pass-through entry
    workflow.add_node("fetch_services", fetch_services)
    workflow.add_node("show_catalog", show_service_catalog)
    workflow.add_node("process_selection", process_service_selection)
    workflow.add_node("send_error", send_service_error)

    # Start at entry for routing
    workflow.set_entry_point("entry")

    # Route based on resume state
    workflow.add_conditional_edges(
        "entry",
        route_service_entry,
        {
            "fetch_services": "fetch_services",
            "process_selection": "process_selection"
        }
    )

    workflow.add_edge("fetch_services", "show_catalog")
    # After showing catalog, END and wait for user input (pause)
    workflow.add_edge("show_catalog", END)

    workflow.add_conditional_edges(
        "process_selection",
        route_after_selection,
        {
            "selection_error": "send_error",
            "selection_success": END
        }
    )

    # Error path: send error and END (don't loop!)
    workflow.add_edge("send_error", END)

    return workflow.compile()
