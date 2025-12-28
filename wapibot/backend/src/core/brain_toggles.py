"""Brain feature toggle checks and strategy getters."""

from typing import Literal
from core.brain_config import get_brain_settings


# Mode checks
def is_shadow_mode() -> bool:
    """Check if brain is in shadow mode (observe only)."""
    return get_brain_settings().brain_mode == "shadow"


def is_reflex_mode() -> bool:
    """Check if brain is in reflex mode (fast, template-based)."""
    return get_brain_settings().brain_mode == "reflex"


def is_conscious_mode() -> bool:
    """Check if brain is in conscious mode (quality, LLM-based)."""
    return get_brain_settings().brain_mode == "conscious"


# Action toggles (conscious mode only)
def can_customize_template() -> bool:
    """Check if brain can customize template messages."""
    settings = get_brain_settings()
    return settings.brain_action_template_customize and is_conscious_mode()


def can_confirm_dates() -> bool:
    """Check if brain can confirm ambiguous dates."""
    settings = get_brain_settings()
    return settings.brain_action_date_confirm


def can_suggest_addons() -> bool:
    """Check if brain can suggest addons."""
    settings = get_brain_settings()
    return settings.brain_action_addon_suggest


def can_answer_qa() -> bool:
    """Check if brain can answer Q&A questions."""
    settings = get_brain_settings()
    return settings.brain_action_qa_answer


def can_handle_bargaining() -> bool:
    """Check if brain can handle price bargaining."""
    settings = get_brain_settings()
    return settings.brain_action_bargaining_handle


def can_escalate_human() -> bool:
    """Check if brain can escalate to human."""
    settings = get_brain_settings()
    return settings.brain_action_escalate_human


def can_cancel_booking() -> bool:
    """Check if brain can process cancellations."""
    settings = get_brain_settings()
    return settings.brain_action_cancel_booking


def can_reset_flow() -> bool:
    """Check if brain can reset/resume flows."""
    settings = get_brain_settings()
    return settings.brain_action_flow_reset


def can_create_dynamic_graph() -> bool:
    """Check if brain can create dynamic workflow nodes."""
    settings = get_brain_settings()
    return settings.brain_action_dynamic_graph


# Strategy getters
def get_retry_strategy() -> int:
    """Get retry count based on brain mode."""
    return 1 if is_reflex_mode() else 3


def get_timeout_strategy() -> float:
    """Get timeout in seconds based on brain mode."""
    return 5.0 if is_reflex_mode() else 10.0


def get_validation_strategy() -> Literal["log", "clear"]:
    """Get validation failure strategy based on brain mode."""
    return "log" if is_reflex_mode() else "clear"
