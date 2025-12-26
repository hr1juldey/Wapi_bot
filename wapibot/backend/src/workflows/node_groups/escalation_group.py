"""Human escalation node group - handles transfer to human support."""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.escalation_message import EscalationMessageBuilder

logger = logging.getLogger(__name__)


async def log_escalation(state: BookingState) -> BookingState:
    """Log escalation for analytics and routing."""
    reason = state.get("escalation_reason", "unknown")
    conversation_id = state.get("conversation_id", "unknown")

    logger.warning(
        f"🚨 ESCALATION: {reason} | Conversation: {conversation_id}"
    )

    state["escalated_to_human"] = True
    state["escalation_timestamp"] = state.get("timestamp")
    return state


async def send_escalation_message(state: BookingState) -> BookingState:
    """Send escalation handoff message."""
    result = await send_message_node(state, EscalationMessageBuilder())
    result["should_proceed"] = False  # Stop automated responses
    result["human_takeover_required"] = True
    return result


def create_escalation_group() -> StateGraph:
    """Create human escalation workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("log", log_escalation)
    workflow.add_node("notify", send_escalation_message)
    workflow.set_entry_point("log")
    workflow.add_edge("log", "notify")
    workflow.add_edge("notify", END)
    return workflow.compile()
