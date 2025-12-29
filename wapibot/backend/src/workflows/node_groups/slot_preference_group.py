"""Slot preference - ask open-ended, hybrid regex+DSPy extraction, incremental MCQ fallback."""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.extraction import extract_slot_preference
from nodes.message_builders.date_preference_prompt import DatePreferencePromptBuilder
from nodes.message_builders.time_preference_menu import TimePreferenceMenuBuilder
from nodes.message_builders.date_preference_menu import DatePreferenceMenuBuilder

logger = logging.getLogger(__name__)


def route_preference_entry(state: BookingState) -> str:
    """Route based on current step."""
    current_step = state.get("current_step", "")
    if current_step == "awaiting_preference":
        logger.info("🔀 Resuming - extracting")
        return "extract_preference"
    elif current_step == "awaiting_time_mcq":
        logger.info("🔀 Resuming - time MCQ")
        return "process_time_mcq"
    elif current_step == "awaiting_date_mcq":
        logger.info("🔀 Resuming - date MCQ")
        return "process_date_mcq"
    else:
        logger.info("🔀 Fresh start - asking")
        return "ask_preference"


async def ask_preference(state: BookingState) -> BookingState:
    """Ask when customer wants to book (open-ended question)."""
    result = await send_message_node(state, DatePreferencePromptBuilder())
    result["should_proceed"] = False
    result["current_step"] = "awaiting_preference"
    return result


async def extract_preference(state: BookingState) -> BookingState:
    """Extract date/time preference (regex + DSPy fallback)."""
    return await extract_slot_preference.node(state)


def route_after_extraction(state: BookingState) -> str:
    """Route based on what was extracted."""
    has_date = bool(state.get("preferred_date"))
    has_time = bool(state.get("preferred_time_range"))

    if has_date and has_time:
        return "both_extracted"
    elif has_date:
        return "date_only"
    elif has_time:
        return "time_only"
    else:
        return "neither"


async def process_time_mcq(state: BookingState) -> BookingState:
    """Process time MCQ selection (1=morning, 2=afternoon, 3=evening)."""
    message = state.get("user_message", "").strip()
    time_map = {"1": "morning", "2": "afternoon", "3": "evening"}
    time_range = time_map.get(message)
    if time_range:
        state["preferred_time_range"] = time_range
        state["slot_preference_extraction_method"] = "menu"
        logger.info(f"✅ Time MCQ: {time_range}")
    else:
        logger.warning(f"⚠️ Invalid time MCQ: {message}")
    return state


async def process_date_mcq(state: BookingState) -> BookingState:
    """Process date MCQ selection (1=today, 2=tomorrow, 3=day after, 4=next week)."""
    from datetime import datetime, timedelta
    message = state.get("user_message", "").strip()
    today = datetime.now().date()
    date_map = {"1": today, "2": today + timedelta(days=1), "3": today + timedelta(days=2), "4": today + timedelta(days=7)}
    selected_date = date_map.get(message)
    if selected_date:
        state["preferred_date"] = selected_date.isoformat()
        state["slot_preference_extraction_method"] = "menu"
        logger.info(f"✅ Date MCQ: {selected_date}")
    else:
        logger.warning(f"⚠️ Invalid date MCQ: {message}")
    return state


async def ask_time_mcq(state: BookingState) -> BookingState:
    """Ask time preference MCQ."""
    result = await send_message_node(state, TimePreferenceMenuBuilder())
    result["should_proceed"] = False
    result["current_step"] = "awaiting_time_mcq"
    return result


async def ask_date_mcq(state: BookingState) -> BookingState:
    """Ask date preference MCQ."""
    result = await send_message_node(state, DatePreferenceMenuBuilder())
    result["should_proceed"] = False
    result["current_step"] = "awaiting_date_mcq"
    return result


def create_slot_preference_group() -> StateGraph:
    """Create slot preference collection workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("entry", lambda s: s)
    workflow.add_node("ask_preference", ask_preference)
    workflow.add_node("extract_preference", extract_preference)
    workflow.add_node("process_time_mcq", process_time_mcq)
    workflow.add_node("process_date_mcq", process_date_mcq)
    workflow.add_node("ask_time_mcq", ask_time_mcq)
    workflow.add_node("ask_date_mcq", ask_date_mcq)
    workflow.set_entry_point("entry")
    workflow.add_conditional_edges("entry", route_preference_entry,
        {"ask_preference": "ask_preference", "extract_preference": "extract_preference", "process_time_mcq": "process_time_mcq", "process_date_mcq": "process_date_mcq"})
    workflow.add_edge("ask_preference", END)
    workflow.add_conditional_edges("extract_preference", route_after_extraction,
        {"both_extracted": END, "date_only": "ask_time_mcq", "time_only": "ask_date_mcq", "neither": "ask_date_mcq"})
    workflow.add_conditional_edges("process_time_mcq", route_after_extraction,
        {"both_extracted": END, "time_only": "ask_date_mcq", "date_only": "ask_time_mcq", "neither": "ask_date_mcq"})
    workflow.add_conditional_edges("process_date_mcq", route_after_extraction,
        {"both_extracted": END, "date_only": "ask_time_mcq", "time_only": "ask_date_mcq", "neither": "ask_date_mcq"})
    workflow.add_edge("ask_time_mcq", END)
    workflow.add_edge("ask_date_mcq", END)
    return workflow.compile()
