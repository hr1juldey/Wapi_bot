"""Brain feature toggle checks."""

from core.brain_config import get_brain_settings


def can_customize_template() -> bool:
    """Check if brain can customize template messages."""
    settings = get_brain_settings()
    return settings.brain_action_template_customize


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
