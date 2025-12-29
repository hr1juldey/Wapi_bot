"""Addon selection - fetch, show options, extract (multiple/skip), validate."""

import logging
import re
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.call_frappe import node as call_frappe_node
from nodes.message_builders.addon_selection import AddonSelectionBuilder
from nodes.routing.resume_router import create_resume_router
from nodes.error_handling.selection_error_handler import handle_selection_error
from clients.frappe_yawlit import get_yawlit_client

logger = logging.getLogger(__name__)


async def fetch_addons(state: BookingState) -> BookingState:
    """Fetch available addons for selected service from Frappe API."""
    client = get_yawlit_client()
    def extract_service_id(s):
        return {"service_id": s.get("selected_service", {}).get("name")}
    logger.info("➕ Fetching optional addons from API...")
    result = await call_frappe_node(state, client.service_catalog.get_optional_addons, "addons_response", state_extractor=extract_service_id)
    addons_response = result.get("addons_response", {})
    addons = addons_response.get("message", {}).get("optional_addons", [])
    result["available_addons"] = addons
    if not addons:
        logger.info("No addons available - auto-skipping")
        result["skipped_addons"] = True
        result["addon_selection_complete"] = True
        result["addon_ids"] = []
    return result


async def show_addon_options(state: BookingState) -> BookingState:
    """Show addon options using message builder."""
    result = await send_message_node(state, AddonSelectionBuilder())

    # Pause and wait for user's selection
    result["should_proceed"] = False
    result["current_step"] = "awaiting_addon_selection"
    return result


async def extract_addon_selection(state: BookingState) -> BookingState:
    """Extract addon selection from user message."""
    user_message = state.get("user_message", "").strip().lower()
    available_addons = state.get("available_addons", [])
    if any(keyword in user_message for keyword in ["none", "skip", "no", "nah"]):
        state["skipped_addons"] = True
        state["addon_selection_complete"] = True
        state["addon_ids"] = []
        state["selected_addons"] = []
        logger.info("➕ User skipped addon selection")
        return state
    selected_indices = []
    selected_addons = []
    numbers = re.findall(r'\d+', user_message)
    for num in numbers:
        try:
            idx = int(num)
            if 1 <= idx <= len(available_addons) and idx not in selected_indices:
                selected_indices.append(idx)
                selected_addons.append(available_addons[idx - 1])
        except ValueError:
            continue
    if selected_indices:
        state["selected_addons"] = selected_addons
        state["addon_ids"] = [{"addon": a.get("name"), "quantity": 1, "unit_price": a.get("unit_price", 0)} for a in selected_addons]
        state["addon_selection_complete"] = True
        state["skipped_addons"] = False
        logger.info(f"➕ Addons selected: {[a.get('addon_name', a.get('name')) for a in selected_addons]} (options {selected_indices})")
    else:
        state["addon_selection_complete"] = False
        logger.warning(f"Could not parse addon selection: {user_message}")
    return state


async def validate_addon_selection(state: BookingState) -> BookingState:
    """Validate that addon selection is complete."""
    if not state.get("addon_selection_complete"):
        logger.warning("Addon selection validation failed")

    return state


async def send_invalid_addon_selection(state: BookingState) -> BookingState:
    """Send message for invalid addon selection."""
    def error_msg(s):
        return f'Please reply with numbers (1-{len(s.get("available_addons", []))}) or "Skip".\nE.g., "1", "1 3", "Skip"'
    return await handle_selection_error(state, awaiting_step="awaiting_addon_selection", error_message_builder=error_msg)


def route_addon_availability(state: BookingState) -> str:
    """Route based on whether addons are available."""
    available_addons = state.get("available_addons", [])
    if not available_addons:
        return "no_addons"  # Skip to END
    else:
        return "show_options"


def route_addon_validation(state: BookingState) -> str:
    """Route based on addon selection validation."""
    if state.get("addon_selection_complete"):
        return "valid"
    else:
        return "invalid"


# Create resume router for entry point
route_addon_entry = create_resume_router(
    awaiting_step="awaiting_addon_selection",
    resume_node="extract_selection",
    fresh_node="fetch_addons",
    readiness_check=lambda s: not s.get("addon_selection_complete", False),
    router_name="addon_entry"
)


def create_addon_group() -> StateGraph:
    """Create addon selection workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("entry", lambda s: s)
    workflow.add_node("fetch_addons", fetch_addons)
    workflow.add_node("show_addon_options", show_addon_options)
    workflow.add_node("extract_addon_selection", extract_addon_selection)
    workflow.add_node("validate_addon_selection", validate_addon_selection)
    workflow.add_node("send_invalid_addon_selection", send_invalid_addon_selection)
    workflow.set_entry_point("entry")
    workflow.add_conditional_edges("entry", route_addon_entry,
        {"fetch_addons": "fetch_addons", "extract_selection": "extract_addon_selection"})
    workflow.add_conditional_edges("fetch_addons", route_addon_availability,
        {"no_addons": END, "show_options": "show_addon_options"})
    workflow.add_edge("show_addon_options", END)
    workflow.add_edge("extract_addon_selection", "validate_addon_selection")
    workflow.add_conditional_edges("validate_addon_selection", route_addon_validation,
        {"valid": END, "invalid": "send_invalid_addon_selection"})
    workflow.add_edge("send_invalid_addon_selection", END)
    return workflow.compile()
