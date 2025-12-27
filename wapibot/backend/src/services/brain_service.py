"""Brain control service layer."""

import logging
from typing import Dict, Any, List
from core.brain_config import get_brain_settings
from core.brain_toggles import (
    can_customize_template,
    can_confirm_dates,
    can_suggest_addons,
    can_answer_qa,
    can_handle_bargaining,
    can_escalate_human,
    can_cancel_booking,
    can_reset_flow,
    can_create_dynamic_graph
)
from repositories.brain_decision_repo import BrainDecisionRepository
from tasks.dream_task import run_dream_cycle
from tasks.gepa_optimization_task import run_gepa_optimization

logger = logging.getLogger(__name__)


class BrainService:
    """Service layer for Brain Control API."""

    def __init__(self):
        """Initialize brain service."""
        self.settings = get_brain_settings()
        self.decision_repo = BrainDecisionRepository()

    async def trigger_dream(self, force: bool = False, min_conversations: int | None = None) -> Dict[str, Any]:
        """Trigger dream cycle."""
        logger.info("🌙 Triggering dream cycle...")
        result = run_dream_cycle.delay()
        return {"task_id": result.id, "status": "queued"}

    async def trigger_training(self, optimizer: str = "gepa", num_iterations: int = 100) -> Dict[str, Any]:
        """Trigger GEPA optimization."""
        logger.info(f"🧠 Triggering {optimizer} optimization...")
        result = run_gepa_optimization.delay(num_iterations)
        return {"task_id": result.id, "status": "queued"}

    async def get_brain_status(self) -> Dict[str, Any]:
        """Get brain system status."""
        return {
            "enabled": self.settings.brain_enabled,
            "mode": self.settings.brain_mode,
            "features": self.get_feature_toggles(),
            "metrics": {
                "dream_enabled": self.settings.dream_enabled,
                "rl_gym_enabled": self.settings.rl_gym_enabled
            }
        }

    def get_feature_toggles(self) -> Dict[str, bool]:
        """Get all feature toggle states."""
        return {
            "template_customize": can_customize_template(),
            "date_confirm": can_confirm_dates(),
            "addon_suggest": can_suggest_addons(),
            "qa_answer": can_answer_qa(),
            "bargaining_handle": can_handle_bargaining(),
            "escalate_human": can_escalate_human(),
            "cancel_booking": can_cancel_booking(),
            "flow_reset": can_reset_flow(),
            "dynamic_graph": can_create_dynamic_graph()
        }

    async def get_recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent brain decisions."""
        decisions = self.decision_repo.get_recent(limit)
        return [d.dict() for d in decisions]


# Singleton instance
_brain_service: BrainService | None = None


def get_brain_service() -> BrainService:
    """Get brain service singleton."""
    global _brain_service
    if _brain_service is None:
        _brain_service = BrainService()
    return _brain_service
