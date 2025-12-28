"""Brain-aware workflow wrapper for shadow mode and telemetry.

Wraps LangGraph workflows to enable:
- Shadow mode: Observe decisions without acting
- Telemetry: Record all brain decisions for learning
- Mode transitions: Automatically switch between reflex/conscious modes

Usage:
    # Create workflow
    workflow = StateGraph(BookingState)
    workflow.add_node("extract", extract_node)
    workflow.add_node("validate", validate_node)

    # Wrap with brain awareness
    brain_workflow = BrainWorkflow(workflow.compile())

    # Execute (automatically handles shadow mode, telemetry)
    final_state = await brain_workflow.ainvoke(initial_state)
"""

import logging
from typing import Dict, Any, Optional
from langgraph.graph.state import CompiledStateGraph
from workflows.shared.state import BookingState
from core.brain_config import get_brain_settings
from core.brain_toggles import is_shadow_mode
from utils.field_utils import get_nested_field, set_nested_field

logger = logging.getLogger(__name__)


class BrainWorkflow:
    """Wrapper for LangGraph workflows with brain awareness.

    Responsibilities:
    - Shadow mode: Execute workflow but don't send messages/call APIs
    - Telemetry: Record all brain decisions
    - Mode detection: Route to reflex vs conscious paths
    """

    def __init__(self, compiled_workflow: CompiledStateGraph):
        """Initialize brain-aware workflow.

        Args:
            compiled_workflow: LangGraph compiled workflow (from workflow.compile())
        """
        self.workflow = compiled_workflow
        self.brain_settings = get_brain_settings()

    async def ainvoke(
        self,
        state: BookingState,
        config: Optional[Dict[str, Any]] = None
    ) -> BookingState:
        """Execute workflow with brain awareness.

        Args:
            state: Initial booking state
            config: Optional LangGraph config

        Returns:
            Final state after workflow execution
        """

        # Check if brain disabled
        if not self.brain_settings.brain_enabled:
            logger.info("🧠 Brain disabled, executing workflow normally")
            return await self.workflow.ainvoke(state, config)

        # Shadow mode: Observe but don't act
        if is_shadow_mode():
            logger.info("👁️ Shadow mode: Observing workflow execution")
            shadow_state = await self._execute_shadow_mode(state, config)
            return shadow_state

        # Normal execution with telemetry
        logger.info(f"🧠 Brain mode: {self.brain_settings.brain_mode}")
        final_state = await self.workflow.ainvoke(state, config)

        # Record telemetry
        await self._record_telemetry(final_state)

        return final_state

    async def _execute_shadow_mode(
        self,
        state: BookingState,
        config: Optional[Dict[str, Any]] = None
    ) -> BookingState:
        """Execute workflow in shadow mode (observe only).

        In shadow mode:
        - Workflow executes normally
        - Observations are recorded
        - Messages are NOT sent
        - APIs are NOT called
        - State is updated only with observations

        Args:
            state: Initial state
            config: Optional config

        Returns:
            State with observations but no actions
        """

        # Mark state as shadow mode
        shadow_state = {**state, "shadow_mode": True}

        # Execute workflow
        result_state = await self.workflow.ainvoke(shadow_state, config)

        # Extract observations (remove action results)
        observations = get_nested_field(result_state, "brain_observations") or {}

        logger.info(
            f"👁️ Shadow mode complete: {len(observations)} observations recorded"
        )

        # Return original state + observations
        final_state = {**state}
        set_nested_field(final_state, "brain_observations", observations)

        return final_state

    async def _record_telemetry(self, state: BookingState) -> None:
        """Record brain telemetry for learning.

        Args:
            state: Final workflow state
        """

        # Check if RL gym enabled
        if not self.brain_settings.rl_gym_enabled:
            return

        # Extract telemetry data
        observations = get_nested_field(state, "brain_observations") or {}

        logger.debug(
            f"📊 Telemetry: {len(observations)} brain observations recorded"
        )

        # TODO: Write to brain_gym.db when RL system implemented