"""Generate dreams atomic node - Ollama-powered synthetic data generation."""

import logging
from typing import Protocol, List, Dict, Any
from models.brain_state import BrainState

logger = logging.getLogger(__name__)


class DreamGenerator(Protocol):
    """Protocol for dream generation (Ollama client)."""

    def generate(self, prompt: str, model: str) -> str:
        """Generate dream using Ollama.

        Args:
            prompt: Dream generation prompt
            model: Ollama model name

        Returns:
            Generated dream scenario
        """
        ...


def node(
    state: BrainState,
    generator: DreamGenerator,
    model: str = "llama3.2",
    hallucination_ratio: float = 0.2
) -> BrainState:
    """Atomic node: Generate synthetic dream scenarios using Ollama.

    Dreams combine:
    - Real memories (80%)
    - Creative hallucinations (20%)
    - Pattern extrapolation
    - "What-if" scenarios

    Args:
        state: Current brain state
        generator: DreamGenerator implementation (Ollama client)
        model: Ollama model name
        hallucination_ratio: Ratio of hallucinated vs real scenarios

    Returns:
        Updated state with generated_dreams field
    """
    try:
        memories = state.get("recalled_memories", [])

        if not memories:
            logger.warning("No memories to dream about")
            state["generated_dreams"] = []
            return state

        # Build dream prompt from memories
        memory_summary = _summarize_memories(memories)

        # Dream prompt (inspired by "Language Models Need Sleep" paper)
        prompt = f"""Based on these conversation patterns, generate 3 creative scenarios:

{memory_summary}

Generate realistic variations:
1. A similar but slightly different booking flow
2. A challenging edge case scenario
3. A creative "what-if" scenario

Format: JSON array of scenarios."""

        # Generate dreams
        dream_text = generator.generate(prompt=prompt, model=model)

        # Parse dreams (TODO: proper JSON parsing)
        state["generated_dreams"] = [
            {"scenario": dream_text, "type": "synthetic"}
        ]

        logger.info(f"Generated {len(state['generated_dreams'])} dream scenarios")

        return state

    except Exception as e:
        logger.error(f"Generate dreams failed: {e}")
        state["generated_dreams"] = []
        return state


def _summarize_memories(memories: List[Dict[str, Any]]) -> str:
    """Summarize memories for dream prompt."""
    summary_lines = []
    for i, mem in enumerate(memories[:5], 1):  # Top 5 memories
        summary_lines.append(
            f"{i}. User: {mem.get('user_message', '')[:50]}... "
            f"→ Satisfaction: {mem.get('user_satisfaction', 0.0):.2f}"
        )
    return "\n".join(summary_lines)
