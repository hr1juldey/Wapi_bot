"""Shadow mode node group - Observe only, never act."""

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
from dspy_modules.module_loader import load_all_modules
from repositories.brain_decision_repo import BrainDecisionRepository
from core.brain_config import get_brain_settings

logger = logging.getLogger(__name__)


def create_shadow_workflow(use_optimized: bool = None) -> StateGraph:
    """Create shadow mode workflow.

    Shadow mode:
    - Observes ALL conversations
    - Processes with brain modules (baseline or optimized)
    - Logs decisions to RL Gym
    - NEVER takes action (no response sent)

    Args:
        use_optimized: Use GEPA-optimized modules (None = from config)

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(BrainState)

    # Get settings
    settings = get_brain_settings()
    if use_optimized is None:
        use_optimized = settings.use_optimized_modules

    # Load brain modules (optimized or baseline)
    modules = load_all_modules(use_optimized=use_optimized)

    conflict_detector = modules["conflict"]
    intent_pred = modules["intent"]
    quality_eval = modules["quality"]
    goal_decomp = modules["goals"]
    response_gen = modules["response"]
    decision_repo = BrainDecisionRepository()

    logger.info(f"🧠 Shadow workflow using {'optimized' if use_optimized else 'baseline'} modules")

    # Add brain processing nodes
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

    # Linear flow: observe → process → log (no action)
    workflow.set_entry_point("monitor_conflict")
    workflow.add_edge("monitor_conflict", "predict_intent")
    workflow.add_edge("predict_intent", "evaluate_quality")
    workflow.add_edge("evaluate_quality", "decompose_goals")
    workflow.add_edge("decompose_goals", "propose_response")
    workflow.add_edge("propose_response", "log_to_gym")
    workflow.set_finish_point("log_to_gym")

    logger.info("Shadow mode workflow created")
    return workflow.compile()
