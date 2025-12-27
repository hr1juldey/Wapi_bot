"""Reflex mode node group - Code dictates LLM (spinal cord mode)."""

import logging
from langgraph.graph import StateGraph
from models.brain_state import BrainState
from nodes.brain import conflict_monitor, log_decision
from dspy_modules.brain import ConflictDetector
from repositories.brain_decision_repo import BrainDecisionRepository

logger = logging.getLogger(__name__)


def route_reflex_action(state: BrainState) -> str:
    """Route based on conflict type in reflex mode.

    Reflex mode hierarchy:
    1. Try regex patterns first
    2. Use template-only responses
    3. Fail fast on uncertainty
    """
    conflict = state.get("conflict_detected")

    if conflict == "bargaining":
        return "handle_bargaining"
    elif conflict == "cancellation":
        return "handle_cancellation"
    elif conflict == "off_topic":
        return "answer_qa"
    elif conflict in ["frustration", "confusion"]:
        return "escalate_human"
    else:
        # No conflict, continue normal flow
        return "continue_workflow"


def create_reflex_workflow() -> StateGraph:
    """Create reflex mode workflow.

    Reflex mode:
    - Code dictates LLM behavior
    - Regex-first extraction
    - Template-only responses
    - No creative LLM generation
    - Fail fast on uncertainty

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(BrainState)

    # Initialize modules
    conflict_detector = ConflictDetector()
    decision_repo = BrainDecisionRepository()

    # Add nodes
    workflow.add_node("monitor_conflict",
        lambda s: conflict_monitor(s, conflict_detector))
    workflow.add_node("log_to_gym",
        lambda s: log_decision(s, decision_repo))

    # Simple reflex routing
    workflow.set_entry_point("monitor_conflict")
    workflow.add_conditional_edges(
        "monitor_conflict",
        route_reflex_action,
        {
            "handle_bargaining": "log_to_gym",  # Delegates to bargaining_group
            "handle_cancellation": "log_to_gym",  # Delegates to cancellation_group
            "answer_qa": "log_to_gym",  # Delegates to qa_group
            "escalate_human": "log_to_gym",  # Delegates to escalation_group
            "continue_workflow": "log_to_gym"  # Continue normal booking flow
        }
    )
    workflow.set_finish_point("log_to_gym")

    logger.info("Reflex mode workflow created")
    return workflow.compile()
