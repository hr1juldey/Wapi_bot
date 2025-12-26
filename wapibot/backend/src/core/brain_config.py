"""Brain system configuration from environment variables."""

from typing import Literal
from pydantic import Field
from core.config import Settings


class BrainSettings(Settings):
    """Brain-specific settings extending base Settings."""

    # Master controls
    brain_enabled: bool = Field(default=True, description="Enable brain observation")
    brain_mode: Literal["shadow", "reflex", "conscious"] = Field(
        default="shadow",
        description="Brain operation mode"
    )

    # Action toggles (conscious mode only)
    brain_action_template_customize: bool = Field(default=True)
    brain_action_date_confirm: bool = Field(default=False)
    brain_action_addon_suggest: bool = Field(default=False)
    brain_action_qa_answer: bool = Field(default=False)
    brain_action_bargaining_handle: bool = Field(default=False)
    brain_action_escalate_human: bool = Field(default=False)
    brain_action_cancel_booking: bool = Field(default=False)
    brain_action_flow_reset: bool = Field(default=False)
    brain_action_dynamic_graph: bool = Field(default=False)

    # Reflex mode settings
    reflex_regex_first: bool = Field(default=True)
    reflex_template_only: bool = Field(default=True)
    reflex_fail_fast: bool = Field(default=True)

    # Dreaming
    dream_enabled: bool = Field(default=True)
    dream_ollama_model: str = Field(default="llama3.2")
    dream_interval_hours: int = Field(default=6)
    dream_min_conversations: int = Field(default=50)
    dream_hallucination_ratio: float = Field(default=0.2)

    # RL Gym
    rl_gym_enabled: bool = Field(default=True)
    rl_gym_db_path: str = Field(default="brain_gym.db")
    rl_gym_log_all: bool = Field(default=True)
    rl_gym_optimize_interval: int = Field(default=100)


_brain_settings: BrainSettings | None = None


def get_brain_settings() -> BrainSettings:
    """Get cached brain settings instance."""
    global _brain_settings
    if _brain_settings is None:
        _brain_settings = BrainSettings()
    return _brain_settings
