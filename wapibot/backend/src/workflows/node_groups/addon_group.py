"""Addon selection node group - displays and processes addon choices."""

import logging
import re
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.addon_catalog import AddonCatalogBuilder
from clients.frappe_yawlit import get_frappe_client

logger = logging.getLogger(__name__)


async def fetch_addons(state: BookingState) -> BookingState:
    """Fetch addons for selected service from API."""
    selected_service = state.get("selected_service", {})
    service_id = selected_service.get("name") or selected_service.get("service_id")

    if not service_id:
        state["available_addons"] = []
        return state

    try:
        client = get_frappe_client()
        result = await client.booking_catalog.get_optional_addons(service_id)
        addons = result.get("message", {}).get("addons", [])
        state["available_addons"] = addons
        logger.info(f"✅ Fetched {len(addons)} addons")
        return state
    except Exception as e:
        logger.error(f"❌ Addon fetch failed: {e}")
        state["available_addons"] = []
        return state


def route_addon_entry(state: BookingState) -> str:
    """Route based on addon availability and resume state."""
    if not state.get("available_addons"):
        state["skipped_addons"] = True
        state["addon_selection_complete"] = True
        return "no_addons"

    if state.get("current_step") == "awaiting_addon_selection":
        return "process_selection"
    return "show_catalog"


async def show_addon_catalog(state: BookingState) -> BookingState:
    """Display addon catalog."""
    result = await send_message_node(state, AddonCatalogBuilder())
    result["should_proceed"] = False
    result["current_step"] = "awaiting_addon_selection"
    return result


async def process_addon_selection(state: BookingState) -> BookingState:
    """Process user's addon selection."""
    message = state.get("user_message", "").strip().lower()
    available_addons = state.get("available_addons", [])

    # Handle skip
    if message in ["skip", "no", "none", "0"]:
        state["selected_addons"] = []
        state["skipped_addons"] = True
        state["addon_selection_complete"] = True
        return state

    # Parse numbers
    numbers = re.findall(r'\d+', message)
    if not numbers:
        state["addon_selection_complete"] = False
        return state

    # Validate and collect selections
    selected_addons = []
    for num in numbers:
        idx = int(num) - 1
        if 0 <= idx < len(available_addons):
            selected_addons.append(available_addons[idx])

    if selected_addons:
        state["selected_addons"] = selected_addons
        state["skipped_addons"] = False
        state["addon_selection_complete"] = True
        logger.info(f"✅ Selected {len(selected_addons)} addons")
    else:
        state["addon_selection_complete"] = False

    return state


def create_addon_group() -> StateGraph:
    """Create addon selection workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("fetch_addons", fetch_addons)
    workflow.add_node("show_catalog", show_addon_catalog)
    workflow.add_node("process_selection", process_addon_selection)
    workflow.set_entry_point("fetch_addons")
    workflow.add_conditional_edges(
        "fetch_addons", route_addon_entry,
        {"no_addons": END, "show_catalog": "show_catalog", "process_selection": "process_selection"}
    )
    workflow.add_edge("show_catalog", END)
    workflow.add_edge("process_selection", END)
    return workflow.compile()
