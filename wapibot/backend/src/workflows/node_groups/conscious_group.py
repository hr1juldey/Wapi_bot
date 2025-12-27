"""Conscious mode node group - LLM dictates code (full brain mode)."""

import logging
from langgraph.graph import StateGraph
from models.brain_state import BrainState
from nodes.brain import (
    conflict_monitor,
    intent_predictor,
    state_evaluator,
    goal_decomposer,
    response_proposer,
    log_decision
)
from dspy_modules.brain import (
    ConflictDetector,
    IntentPredictor,
    QualityEvaluator,
    GoalDecomposer,
    ResponseGenerator
)
from repositories.brain_decision_repo import BrainDecisionRepository
from core.brain_toggles import (
    can_customize_template,
    can_answer_qa,
    can_handle_bargaining,
    can_escalate_human,
    can_cancel_booking
)

logger = logging.getLogger(__name__)


def route_conscious_action(state: BrainState) -> str:
    """Route based on intent and feature toggles.

    Conscious mode:
    - LLM dictates which action to take
    - Feature toggles gate each action
    - Falls back if toggle disabled
    """
    intent = state.get("predicted_intent", "unclear")
    conflict = state.get("conflict_detected")

    # Check feature toggles and route accordingly
    if conflict == "bargaining" and can_handle_bargaining():
        return "handle_bargaining"
    elif conflict == "cancellation" and can_cancel_booking():
        return "handle_cancellation"
    elif conflict == "off_topic" and can_answer_qa():
        return "answer_qa"
    elif conflict in ["frustration", "confusion"] and can_escalate_human():
        return "escalate_human"
    elif intent == "provide_info" and can_customize_template():
        return "propose_response"  # Brain generates custom response
    else:
        return "continue_workflow"  # Fallback to normal flow


def create_conscious_workflow() -> StateGraph:
    """Create conscious mode workflow.

    Conscious mode:
    - Full brain processing pipeline
    - LLM-driven decision making
    - Feature toggles control actions
    - Generates custom responses

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(BrainState)

    # Initialize all brain modules
    conflict_detector = ConflictDetector()
    intent_pred = IntentPredictor()
    quality_eval = QualityEvaluator()
    goal_decomp = GoalDecomposer()
    response_gen = ResponseGenerator()
    decision_repo = BrainDecisionRepository()

    # Add all processing nodes
    workflow.add_node("monitor_conflict",
        lambda s: conflict_monitor(s, conflict_detector))
    workflow.add_node("predict_intent",
        lambda s: intent_predictor(s, intent_pred))
    workflow.add_node("evaluate_quality",
        lambda s: state_evaluator(s, quality_eval))
    workflow.add_node("decompose_goals",
        lambda s: goal_decomposer(s, goal_decomp))
    workflow.add_node("propose_response",
        lambda s: response_proposer(s, response_gen))
    workflow.add_node("log_to_gym",
        lambda s: log_decision(s, decision_repo))

    # Full brain pipeline with conscious routing
    workflow.set_entry_point("monitor_conflict")
    workflow.add_edge("monitor_conflict", "predict_intent")
    workflow.add_edge("predict_intent", "evaluate_quality")
    workflow.add_edge("evaluate_quality", "decompose_goals")
    workflow.add_conditional_edges(
        "decompose_goals",
        route_conscious_action,
        {
            "propose_response": "propose_response",
            "handle_bargaining": "log_to_gym",
            "handle_cancellation": "log_to_gym",
            "answer_qa": "log_to_gym",
            "escalate_human": "log_to_gym",
            "continue_workflow": "log_to_gym"
        }
    )
    workflow.add_edge("propose_response", "log_to_gym")
    workflow.set_finish_point("log_to_gym")

    logger.info("Conscious mode workflow created")
    return workflow.compile()
