"""Atomic response node - generates and sends responses with brain personalization.

SOLID Principles:
- Single Responsibility: ONLY generates and sends responses
- Open/Closed: Extensible via ResponseGenerator Protocol
- Dependency Inversion: Depends on Protocol, not concrete implementations

Blender Design:
- Composes send_message.node() with brain personalization
- Replaces inline response building across node groups
- Supports template-based, LLM-based, and hybrid responses
"""

import logging
from typing import Protocol
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from core.brain_config import get_brain_settings
from core.brain_toggles import can_customize_template

logger = logging.getLogger(__name__)


class ResponseGenerator(Protocol):
    """Protocol for response generators.

    Any callable that takes state and returns a string is a valid ResponseGenerator.
    This includes:
    - MessageBuilder instances (template-based)
    - LLM-based generators
    - Hybrid approaches
    """

    def __call__(self, state: BookingState) -> str:
        """Generate response message from state.

        Args:
            state: Current booking state

        Returns:
            Response message string
        """
        ...


async def node(
    state: BookingState,
    generator: ResponseGenerator,
    allow_brain_personalization: bool = True,
    fallback_message: str = "I'm processing your request..."
) -> BookingState:
    """Atomic response generation node - with optional brain personalization.

    Composes send_message.node() with brain personalization in conscious mode.

    Args:
        state: Current booking state
        generator: ANY callable implementing ResponseGenerator protocol
        allow_brain_personalization: Whether to apply brain customization
        fallback_message: Message to send if generation fails

    Returns:
        Updated state after sending response

    Examples:
        # Template-based response
        from nodes.message_builders.greeting import GreetingBuilder
        await response.node(state, GreetingBuilder())

        # Simple lambda
        await response.node(state, lambda s: f"Hello {s.get('customer', {}).get('first_name')}!")

        # With brain personalization
        await response.node(state, GreetingBuilder(), allow_brain_personalization=True)
    """
    try:
        # Generate base response
        message = generator(state)

        # Brain personalization in conscious mode
        if allow_brain_personalization and can_customize_template():
            brain_settings = get_brain_settings()

            # Check if brain has a proposed response
            proposed_response = state.get("proposed_response")
            brain_confidence = state.get("brain_confidence", 0.0)

            if proposed_response and brain_confidence > 0.8:
                # Use brain's proposed response if high confidence
                logger.info(f"🧠 Using brain-proposed response (confidence: {brain_confidence:.2f})")
                message = proposed_response
            else:
                # Apply brain personalization to template
                # TODO: Integrate with personalize_message.node() in Phase 4 Step 32
                logger.debug(f"🧠 Brain personalization enabled (mode: {brain_settings.brain_mode})")

        # Send response using atomic send_message node
        result = await send_message_node(state, lambda s: message)

        logger.info(f"📤 Response sent: {message[:50]}...")
        return result

    except Exception as e:
        logger.error(f"❌ Response generation failed: {e}")

        # Fallback: send simple error recovery message
        result = await send_message_node(state, lambda s: fallback_message)
        result["response_error"] = str(e)
        return result