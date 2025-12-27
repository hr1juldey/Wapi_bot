"""Dream configuration model."""

from pydantic import BaseModel, Field


class DreamConfig(BaseModel):
    """Configuration for brain dreaming cycles."""

    ollama_model: str = Field(default="llama3.2")
    interval_hours: int = Field(default=6, ge=1)
    min_conversations: int = Field(default=50, ge=1)
    hallucination_ratio: float = Field(default=0.2, ge=0.0, le=1.0)
    max_dreams_per_cycle: int = Field(default=100, ge=1)


class DreamResult(BaseModel):
    """Result of a dreaming cycle."""

    dream_id: str
    timestamp: str
    conversations_processed: int
    dreams_generated: int
    patterns_learned: int
    model_used: str
