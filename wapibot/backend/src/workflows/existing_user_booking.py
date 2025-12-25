"""Existing user booking workflow - MVP demonstrating atomic node composition.

This workflow shows how atomic nodes compose to create complex business logic.

DRY Compliance:
- Uses atomic nodes (send_message, transform, call_api)
- Uses message builders (GreetingBuilder, ServiceCatalogBuilder)
- Uses transformers (FilterServicesByVehicle)
- Uses request builders (FrappeCustomerLookup, FrappeServicesRequest)

SOLID Compliance:
- Workflow orchestration ONLY (no business logic)
- Atomic nodes handle Single Responsibilities
- Builders/transformers are interchangeable (Open/Closed)
"""

from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState

# Atomic nodes
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.transform import node as transform_node
from nodes.atomic.call_api import node as call_api_node

# Message builders
from message_builders.greeting import GreetingBuilder
from message_builders.service_catalog import ServiceCatalogBuilder

# Transformers
from transformers.filter_services import FilterServicesByVehicle

# Request builders
from request_builders.frappe_customer_lookup import FrappeCustomerLookup
from request_builders.frappe_services import FrappeServicesRequest


async def lookup_customer_node(state: BookingState) -> BookingState:
    """Look up customer by phone number."""
    # Use call_api atomic node with FrappeCustomerLookup request builder
    return await call_api_node(
        state,
        FrappeCustomerLookup(),
        "customer_lookup_response"
    )


async def check_customer_exists(state: BookingState) -> str:
    """Route based on customer existence."""
    lookup_response = state.get("customer_lookup_response", {})
    message = lookup_response.get("message", {})

    if message:
        # Customer found - extract data
        state["customer"] = {
            "customer_uuid": message.get("customer_uuid"),
            "first_name": message.get("first_name"),
            "last_name": message.get("last_name"),
            "enabled": message.get("enabled")
        }
        return "existing_customer"
    else:
        return "new_customer"


async def send_greeting_node(state: BookingState) -> BookingState:
    """Send personalized greeting to existing customer."""
    # Use send_message atomic node with GreetingBuilder
    return await send_message_node(
        state,
        GreetingBuilder()
    )


async def send_please_register_node(state: BookingState) -> BookingState:
    """Send registration request to new customer."""
    # Simple message builder inline (could be extracted to message_builders/)
    def please_register(s):
        return "Welcome to Yawlit! To book a service, please register first at https://yawlit.in/register"

    return await send_message_node(
        state,
        please_register
    )


async def fetch_services_node(state: BookingState) -> BookingState:
    """Fetch all services from Frappe."""
    # Use call_api atomic node with FrappeServicesRequest request builder
    result = await call_api_node(
        state,
        FrappeServicesRequest(),
        "services_response"
    )

    # Extract services from response and store in all_services
    services_response = result.get("services_response", {})
    message = services_response.get("message", {})
    services = message.get("services", [])

    result["all_services"] = services

    return result


async def filter_services_node(state: BookingState) -> BookingState:
    """Filter services by vehicle type."""
    # Use transform atomic node with FilterServicesByVehicle transformer
    return await transform_node(
        state,
        FilterServicesByVehicle(),
        "all_services",
        "filtered_services"
    )


async def send_catalog_node(state: BookingState) -> BookingState:
    """Send service catalog to customer."""
    # Use send_message atomic node with ServiceCatalogBuilder
    return await send_message_node(
        state,
        ServiceCatalogBuilder()
    )


def create_existing_user_booking_workflow():
    """Create the existing user booking workflow graph.

    This demonstrates atomic node composition following DRY/SOLID principles.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("lookup_customer", lookup_customer_node)
    workflow.add_node("send_greeting", send_greeting_node)
    workflow.add_node("send_please_register", send_please_register_node)
    workflow.add_node("fetch_services", fetch_services_node)
    workflow.add_node("filter_services", filter_services_node)
    workflow.add_node("send_catalog", send_catalog_node)

    # Set entry point
    workflow.set_entry_point("lookup_customer")

    # Add conditional routing after customer lookup
    workflow.add_conditional_edges(
        "lookup_customer",
        check_customer_exists,
        {
            "existing_customer": "send_greeting",
            "new_customer": "send_please_register"
        }
    )

    # Existing customer flow
    workflow.add_edge("send_greeting", "fetch_services")
    workflow.add_edge("fetch_services", "filter_services")
    workflow.add_edge("filter_services", "send_catalog")
    workflow.add_edge("send_catalog", END)

    # New customer flow ends
    workflow.add_edge("send_please_register", END)

    return workflow.compile()
