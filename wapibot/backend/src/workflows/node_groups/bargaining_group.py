"""Bargaining handler node group - 4-stage price negotiation escalation."""

import logging
import re
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.bargaining_responses import BargainingResponseBuilder
from nodes.brain.conflict_monitor import node as conflict_monitor

logger = logging.getLogger(__name__)


def detect_bargaining(message: str) -> bool:
    """Detect price negotiation attempts."""
    message_lower = message.lower()

    bargaining_patterns = [
        r'\b(discount|cheaper|reduce|lower|less|expensive|costly)\b',
        r'\b(kam|sasta|mehenga)\b',  # Hindi
        r'\b(price.?down|bring.?down)\b',
        r'\b(negotiate|deal|offer)\b'
    ]

    for pattern in bargaining_patterns:
        if re.search(pattern, message_lower):
            return True
    return False


async def initialize_bargaining(state: BookingState) -> BookingState:
    """Initialize bargaining tracking."""
    if "bargaining_stage" not in state:
        state["bargaining_stage"] = 1
    if "bargaining_count" not in state:
        state["bargaining_count"] = 0

    state["bargaining_count"] += 1
    logger.info(f"💰 Bargaining attempt #{state['bargaining_count']}")
    return state


async def send_bargaining_response(state: BookingState) -> BookingState:
    """Send response based on current bargaining stage."""
    result = await send_message_node(state, BargainingResponseBuilder())
    result["bargaining_handled"] = True

    # Escalate stage for next attempt
    current_stage = result.get("bargaining_stage", 1)
    if current_stage < 4:
        result["bargaining_stage"] = current_stage + 1
        result["should_proceed"] = True  # Continue conversation
    else:
        result["should_escalate_human"] = True  # Trigger escalation
        result["should_proceed"] = False  # Pause for escalation

    return result


def route_bargaining_stage(state: BookingState) -> str:
    """Route based on bargaining stage."""
    stage = state.get("bargaining_stage", 1)

    if stage >= 4:
        return "escalate"
    return "respond"


async def mark_for_escalation(state: BookingState) -> BookingState:
    """Mark conversation for human escalation."""
    state["should_escalate_human"] = True
    state["escalation_reason"] = "price_negotiation"
    logger.info("🚨 Escalating to human for price negotiation")
    return state


def create_bargaining_group() -> StateGraph:
    """Create bargaining handler workflow with brain conflict detection."""
    workflow = StateGraph(BookingState)
    workflow.add_node("detect_conflict", conflict_monitor)  # Brain detects bargaining/frustration FIRST
    workflow.add_node("initialize", initialize_bargaining)
    workflow.add_node("respond", send_bargaining_response)
    workflow.add_node("escalate", mark_for_escalation)
    workflow.set_entry_point("detect_conflict")  # Brain observes before any action
    workflow.add_edge("detect_conflict", "initialize")
    workflow.add_conditional_edges(
        "initialize", route_bargaining_stage,
        {"respond": "respond", "escalate": "escalate"}
    )
    workflow.add_edge("respond", END)
    workflow.add_edge("escalate", END)
    return workflow.compile()
