"""Cancellation policy node group - handles booking cancellations with policy checks."""

import logging
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node

logger = logging.getLogger(__name__)


async def check_cancellation_policy(state: BookingState) -> BookingState:
    """Check if cancellation is within free cancellation window."""
    from core.config import get_settings

    settings = get_settings()
    free_cancel_hours = settings.CANCELLATION_FREE_HOURS or 24

    appointment = state.get("appointment") or state.get("slot", {})
    appointment_date_str = appointment.get("date", "")
    appointment_time_str = appointment.get("time_slot", "").split("-")[0].strip()

    if not appointment_date_str:
        state["can_cancel_free"] = False
        state["cancellation_message"] = "No booking found to cancel."
        return state

    try:
        # Parse appointment datetime
        appointment_dt = datetime.fromisoformat(f"{appointment_date_str}T{appointment_time_str}")
        now = datetime.now()
        hours_until = (appointment_dt - now).total_seconds() / 3600

        if hours_until >= free_cancel_hours:
            state["can_cancel_free"] = True
            state["cancellation_message"] = (
                f"✅ Free cancellation available!\n\n"
                f"Appointment: {appointment_date_str} at {appointment_time_str}\n"
                f"Time remaining: {int(hours_until)} hours\n\n"
                f"Reply *CONFIRM* to cancel."
            )
        else:
            state["can_cancel_free"] = False
            state["cancellation_message"] = (
                f"⚠️ Cancellation Policy\n\n"
                f"Free cancellation: {free_cancel_hours}+ hours before\n"
                f"Your booking: {int(hours_until)} hours away\n\n"
                f"Cancellation may incur charges.\n"
                f"Proceed? Reply *YES* or *NO*"
            )
        logger.info(f"📅 Cancellation check: {hours_until:.1f}h until appointment")
        return state

    except Exception as e:
        logger.error(f"❌ Cancellation check failed: {e}")
        state["can_cancel_free"] = False
        state["cancellation_message"] = "Unable to process cancellation. Please contact support."
        return state


async def send_cancellation_message(state: BookingState) -> BookingState:
    """Send cancellation policy message."""
    message = state.get("cancellation_message", "")
    if message:
        state["response"] = message
        state["should_proceed"] = False
        state["current_step"] = "awaiting_cancellation_confirmation"
    return state


def create_cancellation_group() -> StateGraph:
    """Create cancellation policy workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("check_policy", check_cancellation_policy)
    workflow.add_node("send_message", send_cancellation_message)
    workflow.set_entry_point("check_policy")
    workflow.add_edge("check_policy", "send_message")
    workflow.add_edge("send_message", END)
    return workflow.compile()
