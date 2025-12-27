"""Resume/reset flow node group - handles workflow restart choices."""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.resume_prompt import ResumePromptBuilder

logger = logging.getLogger(__name__)


async def show_resume_prompt(state: BookingState) -> BookingState:
    """Show resume/reset choice to user."""
    result = await send_message_node(state, ResumePromptBuilder())
    result["current_step"] = "awaiting_resume_choice"
    result["should_proceed"] = False
    return result


async def process_resume_choice(state: BookingState) -> BookingState:
    """Process user's resume/reset choice."""
    message = state.get("user_message", "").strip().lower()

    if message in ["1", "resume", "continue", "yes"]:
        state["flow_action"] = "resume"
        state["should_proceed"] = True
        logger.info("✅ User chose to RESUME booking")
    elif message in ["2", "reset", "restart", "new", "no"]:
        state["flow_action"] = "reset"
        # Clear booking data
        state["customer"] = None
        state["vehicle"] = None
        state["selected_service"] = None
        state["appointment"] = None
        state["slot"] = None
        state["should_proceed"] = True
        logger.info("🔄 User chose to RESET booking")
    else:
        state["flow_action"] = "invalid"
        state["should_proceed"] = False
        logger.warning(f"⚠️ Invalid resume choice: {message}")

    return state


def create_resume_reset_group() -> StateGraph:
    """Create resume/reset flow workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("show_prompt", show_resume_prompt)
    workflow.add_node("process_choice", process_resume_choice)
    workflow.set_entry_point("show_prompt")
    workflow.add_edge("show_prompt", END)
    workflow.add_edge("process_choice", END)
    return workflow.compile()
