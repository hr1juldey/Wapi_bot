"""Brain Control API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from models.brain_schemas import (
    DreamTriggerRequest,
    TrainTriggerRequest,
    BrainStatusResponse
)
from services.brain_service import get_brain_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/brain", tags=["Brain Control"])


@router.post(
    "/dream",
    summary="Trigger brain dream cycle",
    responses={
        200: {"description": "Dream cycle triggered successfully"},
        500: {"description": "Dream trigger failed"},
    },
)
async def trigger_dream_cycle(request: DreamTriggerRequest):
    """Manually trigger brain dream cycle.

    Brain "dreams" by analyzing conversation patterns and updating decision strategies.
    Normally runs every 6 hours with 50+ conversations, but can be manually triggered.
    """
    try:
        service = get_brain_service()
        result = await service.trigger_dream(request.force, request.min_conversations)
        return result
    except Exception as e:
        logger.error(f"Dream trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/train",
    summary="Trigger GEPA optimization",
    responses={
        200: {"description": "Training triggered successfully"},
        500: {"description": "Training trigger failed"},
    },
)
async def trigger_training(request: TrainTriggerRequest):
    """Trigger GEPA optimization for brain decision-making.

    Optimizes brain's DSPy signatures using GEPA optimizer.
    Use after significant template changes or to improve extraction accuracy.
    """
    try:
        service = get_brain_service()
        result = await service.trigger_training(request.optimizer, request.num_iterations)
        return result
    except Exception as e:
        logger.error(f"Training trigger failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status",
    response_model=BrainStatusResponse,
    summary="Get brain system status",
    responses={
        200: {"description": "Brain status retrieved successfully"},
        500: {"description": "Status fetch failed"},
    },
)
async def get_brain_status():
    """Get brain system status and metrics.

    Returns current operation mode, feature toggles, decision counts, and last dream time.
    """
    try:
        service = get_brain_service()
        return await service.get_brain_status()
    except Exception as e:
        logger.error(f"Status fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/features",
    summary="Get feature toggle states",
    responses={
        200: {"description": "Feature toggles retrieved successfully"},
        500: {"description": "Feature fetch failed"},
    },
)
async def get_feature_toggles():
    """Get all feature toggle states.

    Returns current enabled/disabled state of brain_enabled, rl_gym_enabled, dream_enabled, etc.
    """
    try:
        service = get_brain_service()
        return service.get_feature_toggles()
    except Exception as e:
        logger.error(f"Feature fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/decisions",
    summary="Get recent brain decisions",
    responses={
        200: {"description": "Decisions retrieved successfully"},
        500: {"description": "Decisions fetch failed"},
    },
)
async def get_recent_decisions(limit: int = 100):
    """Get recent brain decisions from RL Gym.

    Returns recent decisions showing conflicts detected, actions taken, and confidence scores.
    Useful for debugging brain behavior and understanding decision patterns.
    """
    try:
        service = get_brain_service()
        decisions = await service.get_recent_decisions(limit)
        return {"decisions": decisions, "total": len(decisions)}
    except Exception as e:
        logger.error(f"Decisions fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
