"""Main brain node group - Routes to appropriate brain mode."""

import logging
from langgraph.graph import StateGraph
from models.brain_state import BrainState
from workflows.node_groups.shadow_group import create_shadow_workflow
from workflows.node_groups.reflex_group import create_reflex_workflow
from workflows.node_groups.conscious_group import create_conscious_workflow
from core.brain_config import get_brain_settings

logger = logging.getLogger(__name__)


def route_brain_mode(state: BrainState) -> str:
    """Route to appropriate brain mode based on config.

    Routes:
    - shadow: Observe and log only
    - reflex: Code dictates LLM
    - conscious: LLM dictates code

    Returns:
        Mode name: "shadow", "reflex", or "conscious"
    """
    settings = get_brain_settings()

    if not settings.brain_enabled:
        logger.info("Brain disabled, skipping processing")
        return "skip"

    mode = settings.brain_mode
    logger.info(f"Brain mode: {mode}")
    return mode


def create_brain_workflow() -> StateGraph:
    """Create main brain workflow with mode routing.

    Architecture:
    - Entry point routes to mode-specific sub-workflow
    - Each mode has different behavior:
        * Shadow: Full observation, no action
        * Reflex: Rule-based, template-only
        * Conscious: LLM-driven, feature-gated
    - All modes log to RL Gym

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(BrainState)

    # Create mode-specific sub-workflows
    shadow_wf = create_shadow_workflow()
    reflex_wf = create_reflex_workflow()
    conscious_wf = create_conscious_workflow()

    # Add mode nodes (sub-workflows)
    workflow.add_node("shadow", lambda s: shadow_wf.invoke(s))
    workflow.add_node("reflex", lambda s: reflex_wf.invoke(s))
    workflow.add_node("conscious", lambda s: conscious_wf.invoke(s))

    # Add skip node for when brain is disabled
    def skip_brain(state: BrainState) -> BrainState:
        """No-op when brain is disabled."""
        logger.info("Brain processing skipped")
        return state

    workflow.add_node("skip", skip_brain)

    # Route to appropriate mode
    workflow.add_conditional_edges(
        "__start__",
        route_brain_mode,
        {
            "shadow": "shadow",
            "reflex": "reflex",
            "conscious": "conscious",
            "skip": "skip"
        }
    )

    # All modes finish
    workflow.add_edge("shadow", "__end__")
    workflow.add_edge("reflex", "__end__")
    workflow.add_edge("conscious", "__end__")
    workflow.add_edge("skip", "__end__")

    logger.info("Main brain workflow created")
    return workflow.compile()
