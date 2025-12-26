"""Profile node group - customer lookup and validation.

This node group handles:
1. Fetching complete customer profile (profile + vehicles + addresses)
2. Validating profile completeness
3. Auto-selecting vehicle if only one exists
4. Routing to appropriate next step

Replaces 7 old nodes:
- lookup_customer
- check_customer_exists
- check_profile_complete
- get_profile
- fetch_vehicles
- check_profile_status
- route_profile_check
"""

from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.profile.fetch_profile import fetch_complete_profile
from nodes.profile.validate_profile import route_after_profile_fetch
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.greeting import GreetingBuilder
from nodes.message_builders.vehicle_options import VehicleOptionsBuilder


async def send_greeting(state: BookingState) -> BookingState:
    """Send personalized greeting message."""
    result = await send_message_node(state, GreetingBuilder())
    result["should_proceed"] = True  # Profile ready, continue to vehicle selection
    return result


async def send_vehicle_options(state: BookingState) -> BookingState:
    """Send vehicle selection options."""
    result = await send_message_node(state, VehicleOptionsBuilder())
    result["should_proceed"] = False  # Need user input, stop here
    result["current_step"] = "awaiting_vehicle_selection"  # Resume at vehicle selection
    return result


async def send_please_register(state: BookingState) -> BookingState:
    """Send registration prompt."""
    message = lambda s: "Please register first: https://yawlit.duckdns.org/customer/auth/register"
    result = await send_message_node(state, message)
    result["should_proceed"] = False  # Error state, stop workflow
    return result


async def send_profile_incomplete(state: BookingState) -> BookingState:
    """Send profile completion prompt."""
    message = lambda s: "Please complete your profile at https://yawlit.duckdns.org/customer/profile"
    result = await send_message_node(state, message)
    result["should_proceed"] = False  # Error state, stop workflow
    return result


async def send_no_vehicles(state: BookingState) -> BookingState:
    """Send vehicle addition prompt."""
    message = lambda s: "Please add a vehicle at https://yawlit.duckdns.org/customer/profile"
    result = await send_message_node(state, message)
    result["should_proceed"] = False  # Error state, stop workflow
    return result


def create_profile_group() -> StateGraph:
    """Create profile check node group.

    Inputs:
    - state["conversation_id"]: Phone number

    Outputs:
    - state["customer"]: Customer data
    - state["vehicle"]: Selected vehicle (or None)
    - state["vehicle_options"]: Vehicle options (or [])
    - state["profile_complete"]: Boolean flag

    Exit Routes:
    - "customer_not_found": No customer exists
    - "profile_incomplete": Profile needs completion
    - "no_vehicles": No vehicles registered
    - "profile_ready": Ready for service selection
    """
    workflow = StateGraph(BookingState)

    # Core nodes
    workflow.add_node("fetch_profile", fetch_complete_profile)
    workflow.add_node("send_greeting", send_greeting)
    workflow.add_node("send_vehicle_options", send_vehicle_options)
    workflow.add_node("send_please_register", send_please_register)
    workflow.add_node("send_profile_incomplete", send_profile_incomplete)
    workflow.add_node("send_no_vehicles", send_no_vehicles)

    # Entry point
    workflow.set_entry_point("fetch_profile")

    # Routing after profile fetch
    workflow.add_conditional_edges(
        "fetch_profile",
        route_after_profile_fetch,
        {
            "customer_not_found": "send_please_register",
            "profile_incomplete": "send_profile_incomplete",
            "no_vehicles": "send_no_vehicles",
            "vehicle_selection_required": "send_vehicle_options",
            "profile_ready": "send_greeting"
        }
    )

    # Terminal nodes
    workflow.add_edge("send_please_register", END)
    workflow.add_edge("send_profile_incomplete", END)
    workflow.add_edge("send_no_vehicles", END)
    workflow.add_edge("send_vehicle_options", END)
    workflow.add_edge("send_greeting", END)

    return workflow.compile()
