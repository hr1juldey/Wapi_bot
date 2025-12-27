"""Celery task for brain dreaming cycles."""

import logging
from datetime import datetime
from tasks import celery_app
from repositories.brain_decision_repo import BrainDecisionRepository
from repositories.brain_dream_repo import BrainDreamRepository
from models.dream_config import DreamResult
from core.brain_config import get_brain_settings

logger = logging.getLogger(__name__)


@celery_app.task(name="brain.dream_cycle")
def run_dream_cycle() -> dict:
    """Execute brain dreaming cycle using Ollama.

    Generates synthetic conversations for self-improvement.

    Returns:
        Dict with dream cycle results
    """
    try:
        settings = get_brain_settings()

        if not settings.dream_enabled:
            logger.info("⏭️ Dreaming disabled in config")
            return {"status": "skipped", "reason": "disabled"}

        # Get recent decisions for dreaming
        decision_repo = BrainDecisionRepository()
        recent_decisions = decision_repo.get_recent(settings.dream_min_conversations)

        if len(recent_decisions) < settings.dream_min_conversations:
            logger.info(f"⏳ Not enough data: {len(recent_decisions)}/{settings.dream_min_conversations}")
            return {"status": "skipped", "reason": "insufficient_data"}

        # TODO: Implement Ollama-based dream generation
        # For now, just log the cycle
        dream_id = f"dream_{datetime.now().timestamp()}"
        dream_result = DreamResult(
            dream_id=dream_id,
            timestamp=datetime.now().isoformat(),
            conversations_processed=len(recent_decisions),
            dreams_generated=0,
            patterns_learned=0,
            model_used=settings.dream_ollama_model
        )

        # Save dream result
        dream_repo = BrainDreamRepository()
        dream_repo.save(dream_result)

        logger.info(f"💤 Dream cycle completed: {dream_id}")
        return {"status": "success", "dream_id": dream_id}

    except Exception as e:
        logger.error(f"❌ Dream cycle failed: {e}")
        return {"status": "error", "error": str(e)}
