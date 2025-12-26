"""Brain mode routing logic - routes to appropriate brain mode."""

from typing import Literal
from core.brain_config import get_brain_settings


def get_brain_mode() -> Literal["shadow", "reflex", "conscious"]:
    """Get current brain operation mode from config."""
    settings = get_brain_settings()
    return settings.brain_mode


def should_brain_act() -> bool:
    """Check if brain should take action (not in shadow mode)."""
    mode = get_brain_mode()
    return mode in ["reflex", "conscious"]


def should_use_llm_decision() -> bool:
    """Check if brain should use LLM for decision making."""
    mode = get_brain_mode()
    return mode == "conscious"


def should_use_code_decision() -> bool:
    """Check if brain should use code-based decision making."""
    mode = get_brain_mode()
    return mode == "reflex"


def route_brain_mode(conflict: str | None, intent: str | None) -> str:
    """Route to appropriate brain action based on mode and inputs.

    Args:
        conflict: Detected conflict type (frustration, bargaining, etc.)
        intent: Predicted user intent

    Returns:
        Action route: "shadow", "reflex", or "conscious"
    """
    settings = get_brain_settings()
    mode = settings.brain_mode

    if mode == "shadow":
        return "shadow"  # Always observe only

    # Reflex mode: Code dictates LLM
    if mode == "reflex":
        if conflict or intent:
            return "reflex"
        return "shadow"

    # Conscious mode: LLM dictates code (with toggles)
    if mode == "conscious":
        return "conscious"

    return "shadow"  # Default to safe mode
