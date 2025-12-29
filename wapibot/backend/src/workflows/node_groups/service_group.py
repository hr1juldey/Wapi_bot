"""Service selection node group - fetch catalog, display, process selection, handle errors."""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.selection.generic_handler import handle_selection, route_after_selection
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.call_frappe import node as call_frappe_node
from nodes.message_builders.service_catalog import ServiceCatalogBuilder
from nodes.routing.resume_router import create_resume_router
from nodes.error_handling.selection_error_handler import handle_selection_error
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
    return await handle_selection_error(
        state,
        awaiting_step="awaiting_service_selection"
    )


# Create resume router for entry point
route_service_entry = create_resume_router(
    awaiting_step="awaiting_service_selection",
    resume_node="process_selection",
    fresh_node="fetch_services",
    readiness_check=lambda s: bool(s.get("service_options")),
    router_name="service_entry"
)


def create_service_group() -> StateGraph:
    """Create service selection workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("entry", lambda s: s)
    workflow.add_node("fetch_services", fetch_services)
    workflow.add_node("show_catalog", show_service_catalog)
    workflow.add_node("process_selection", process_service_selection)
    workflow.add_node("send_error", send_service_error)
    workflow.set_entry_point("entry")
    workflow.add_conditional_edges("entry", route_service_entry,
        {"fetch_services": "fetch_services", "process_selection": "process_selection"})
    workflow.add_edge("fetch_services", "show_catalog")
    workflow.add_edge("show_catalog", END)
    workflow.add_conditional_edges("process_selection", route_after_selection,
        {"selection_error": "send_error", "selection_success": END})
    workflow.add_edge("send_error", END)
    return workflow.compile()
