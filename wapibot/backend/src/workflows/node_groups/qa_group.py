"""Q&A support node group - handles off-topic questions."""

import logging
import re
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.qa_response import QAResponseBuilder

logger = logging.getLogger(__name__)


def detect_question_type(message: str) -> str:
    """Detect question type from message."""
    message_lower = message.lower()

    hours_patterns = [
        r'\b(hours?|timing?|time|open|close|when)\b',
        r'\b(kab khule|kab band)\b'  # Hindi
    ]

    location_patterns = [
        r'\b(where|location|address|area|place)\b',
        r'\b(kaha|kahaan)\b'  # Hindi
    ]

    services_patterns = [
        r'\b(what services|which services|services|offerings|what do you|what can)\b',
        r'\b(kya services|kaun si services)\b'  # Hindi
    ]

    for pattern in hours_patterns:
        if re.search(pattern, message_lower):
            return "hours"

    for pattern in location_patterns:
        if re.search(pattern, message_lower):
            return "location"

    for pattern in services_patterns:
        if re.search(pattern, message_lower):
            return "services"

    return "general"


async def classify_question(state: BookingState) -> BookingState:
    """Classify user's question."""
    message = state.get("user_message", "")
    question_type = detect_question_type(message)
    state["qa_question_type"] = question_type
    logger.info(f"📝 Detected question type: {question_type}")
    return state


async def send_qa_response(state: BookingState) -> BookingState:
    """Send Q&A response."""
    result = await send_message_node(state, QAResponseBuilder())
    result["qa_handled"] = True
    result["should_proceed"] = True  # Continue to booking flow
    return result


def create_qa_group() -> StateGraph:
    """Create Q&A support workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("classify", classify_question)
    workflow.add_node("respond", send_qa_response)
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "respond")
    workflow.add_edge("respond", END)
    return workflow.compile()
