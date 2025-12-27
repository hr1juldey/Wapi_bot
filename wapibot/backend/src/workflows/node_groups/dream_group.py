"""Dream node group - Scheduled dreaming workflow for Celery."""

import logging
import requests
from langgraph.graph import StateGraph
from models.brain_state import BrainState
from nodes.brain import recall_memories, generate_dreams
from repositories.brain_memory_repo import BrainMemoryRepository
from core.brain_config import get_brain_settings

logger = logging.getLogger(__name__)


class OllamaDreamGenerator:
    """Ollama client for dream generation."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama client.

        Args:
            base_url: Ollama API base URL
        """
        self.base_url = base_url

    def generate(self, prompt: str, model: str) -> str:
        """Generate dream using Ollama.

        Args:
            prompt: Dream generation prompt
            model: Ollama model name (e.g., "llama3.2")

        Returns:
            Generated dream text
        """
        try:
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.9,  # High for creativity
                        "top_p": 0.95,
                        "num_predict": 500
                    }
                },
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            dream_text = result.get("response", "")

            logger.info(f"✨ Generated dream ({len(dream_text)} chars) using {model}")
            return dream_text

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ollama API call failed: {e}")
            return f"Dream scenario: {prompt[:100]}... (generation failed)"
        except Exception as e:
            logger.error(f"❌ Dream generation failed: {e}")
            return f"Dream scenario: {prompt[:100]}... (error: {e})"


def route_dream_action(state: BrainState) -> str:
    """Route based on whether dreaming is possible.

    Returns:
        "generate" if enough memories, "skip" otherwise
    """
    can_dream = state.get("can_dream", False)
    return "generate" if can_dream else "skip"


def create_dream_workflow() -> StateGraph:
    """Create dream cycle workflow.

    Dream cycle:
    1. Recall memories from RL Gym
    2. Check if enough data (min 50 conversations)
    3. Generate synthetic scenarios using Ollama
    4. Apply learnings to brain modules (TODO: GEPA optimization)

    This workflow runs on a schedule (Celery task), NOT during conversations.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(BrainState)

    # Initialize components
    settings = get_brain_settings()
    memory_repo = BrainMemoryRepository()
    dream_gen = OllamaDreamGenerator()

    # Add nodes
    workflow.add_node("recall",
        lambda s: recall_memories(
            s,
            memory_repo,
            min_memories=settings.dream_min_conversations
        ))

    workflow.add_node("generate",
        lambda s: generate_dreams(
            s,
            dream_gen,
            model=settings.dream_ollama_model,
            hallucination_ratio=settings.dream_hallucination_ratio
        ))

    def skip_dream(state: BrainState) -> BrainState:
        """Skip dream generation if not enough memories."""
        logger.info("Not enough memories for dreaming")
        state["dream_status"] = "skipped"
        return state

    workflow.add_node("skip", skip_dream)

    # Dream flow: recall → check → generate (or skip)
    workflow.set_entry_point("recall")
    workflow.add_conditional_edges(
        "recall",
        route_dream_action,
        {
            "generate": "generate",
            "skip": "skip"
        }
    )
    workflow.add_edge("generate", "__end__")
    workflow.add_edge("skip", "__end__")

    logger.info("Dream workflow created")
    return workflow.compile()
