"""Existing user booking workflow - Blender-style composition.

This workflow is a COMPOSITION of 9 node groups:
1. Profile Group: Customer lookup + validation
2. Vehicle Group: Vehicle selection (if needed)
3. Address Group: Address selection (if multiple addresses)
4. Service Group: Service catalog + selection
5. Addon Group: Optional service addon selection
6. Slot Preference Group: Ask when to book (smart filtering)
7. Slot Group: Appointment slot selection (filtered & grouped)
8. Utilities Group: Electricity/water availability collection
9. Booking Group: Price calculation + confirmation + creation

Each group is a mini-workflow (subgraph) that can be:
- Tested independently
- Reused in other workflows
- Modified without affecting others

This file is just the orchestrator - it chains groups together.

Architecture Benefits:
- Entry router enables resuming from correct step
- 9 composable node groups (vs 29 loose nodes)
- Zero code duplication
- Each group < 120 lines
- Easy to test and maintain

Previous monolithic version backed up to: existing_user_booking_OLD_MONOLITH.py
"""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from core.checkpointer import checkpointer_manager

# Import node groups (mini-workflows)
from workflows.node_groups.profile_group import create_profile_group
from workflows.node_groups.vehicle_group import create_vehicle_group
from workflows.node_groups.address_group import create_address_group
from workflows.node_groups.service_group import create_service_group
from workflows.node_groups.addon_group import create_addon_group
from workflows.node_groups.slot_preference_group import create_slot_preference_group
from workflows.node_groups.slot_group import create_slot_group
from workflows.node_groups.utilities_group import create_utilities_group
from workflows.node_groups.booking_group import create_booking_group

logger = logging.getLogger(__name__)


def route_entry(state: BookingState) -> str:
    """Route to correct step based on current_step.

    This enables resuming conversations from where they left off.
    """
    current_step = state.get("current_step", "")
    logger.info(f"🔀 Entry router: current_step = '{current_step}'")

    # Route based on where we left off
    if current_step == "awaiting_utilities":
        logger.info("🔀 Resuming at utilities_collection")
        return "utilities_collection"
    elif current_step == "awaiting_slot_selection":
        logger.info("🔀 Resuming at slot_selection")
        return "slot_selection"
    elif current_step == "awaiting_booking_confirmation":
        logger.info("🔀 Resuming at booking_confirmation")
        return "booking_confirmation"
    elif current_step in ["awaiting_preference", "awaiting_time_mcq", "awaiting_date_mcq"]:
        logger.info("🔀 Resuming at slot_preference")
        return "slot_preference"
    elif current_step == "awaiting_addon_selection":
        logger.info("🔀 Resuming at addon_selection")
        return "addon_selection"
    elif current_step == "awaiting_service_selection":
        logger.info("🔀 Resuming at service_selection")
        return "service_selection"
    elif current_step == "awaiting_address_selection":
        logger.info("🔀 Resuming at address_selection")
        return "address_selection"
    elif current_step == "awaiting_vehicle_selection":
        logger.info("🔀 Resuming at vehicle_selection")
        return "vehicle_selection"
    else:
        # Fresh start or unknown step
        logger.info("🔀 Starting fresh at profile_check")
        return "profile_check"


def should_continue(state: BookingState) -> str:
    """Check if workflow should continue or end after each node group.

    Returns:
        - "continue": Proceed to next node group
        - "end": Stop workflow (error occurred or completed)
    """
    return "continue" if state.get("should_proceed", True) else "end"


async def entry_router(state: BookingState) -> BookingState:
    """Entry point that resets should_proceed for resuming."""
    state["should_proceed"] = True
    return state


def create_existing_user_booking_workflow():
    """Create existing user booking workflow.

    Architecture:
    - Entry router enables resuming from correct step
    - 9 composable node groups (like Blender's Geometry Nodes)
    - Each group is self-contained mini-workflow
    - Main graph just chains groups together

    Workflow Flow:
    Profile → Vehicle → Address → Service → Addon → Slot Preference → Slot → Utilities → Booking

    Returns:
        Compiled LangGraph workflow with checkpointing
    """
    workflow = StateGraph(BookingState)

    # Entry router to handle resumption
    workflow.add_node("entry_router", entry_router)

    # Add node groups as composable units
    workflow.add_node("profile_check", create_profile_group())
    workflow.add_node("vehicle_selection", create_vehicle_group())
    workflow.add_node("address_selection", create_address_group())
    workflow.add_node("service_selection", create_service_group())
    workflow.add_node("addon_selection", create_addon_group())
    workflow.add_node("slot_preference", create_slot_preference_group())
    workflow.add_node("slot_selection", create_slot_group())
    workflow.add_node("utilities_collection", create_utilities_group())
    workflow.add_node("booking_confirmation", create_booking_group())

    # Start at entry router
    workflow.set_entry_point("entry_router")

    # Entry router routes to correct step
    workflow.add_conditional_edges(
        "entry_router",
        route_entry,
        {
            "profile_check": "profile_check",
            "vehicle_selection": "vehicle_selection",
            "address_selection": "address_selection",
            "service_selection": "service_selection",
            "addon_selection": "addon_selection",
            "slot_preference": "slot_preference",
            "slot_selection": "slot_selection",
            "utilities_collection": "utilities_collection",
            "booking_confirmation": "booking_confirmation"
        }
    )

    # Chain groups with conditional routing (stop on error)
    workflow.add_conditional_edges(
        "profile_check",
        should_continue,
        {"continue": "vehicle_selection", "end": END}
    )

    workflow.add_conditional_edges(
        "vehicle_selection",
        should_continue,
        {"continue": "address_selection", "end": END}
    )

    workflow.add_conditional_edges(
        "address_selection",
        should_continue,
        {"continue": "service_selection", "end": END}
    )

    workflow.add_conditional_edges(
        "service_selection",
        should_continue,
        {"continue": "addon_selection", "end": END}
    )

    workflow.add_conditional_edges(
        "addon_selection",
        should_continue,
        {"continue": "slot_preference", "end": END}
    )

    workflow.add_conditional_edges(
        "slot_preference",
        should_continue,
        {"continue": "slot_selection", "end": END}
    )

    workflow.add_conditional_edges(
        "slot_selection",
        should_continue,
        {"continue": "utilities_collection", "end": END}
    )

    workflow.add_conditional_edges(
        "utilities_collection",
        should_continue,
        {"continue": "booking_confirmation", "end": END}
    )

    workflow.add_edge("booking_confirmation", END)

    # Compile with checkpointing (checkpointer initialized in main.py lifespan)
    return workflow.compile(checkpointer=checkpointer_manager.memory)
