"""Atomic send message node - works with ANY message builder.

SOLID Principles:
- Single Responsibility: ONLY sends WhatsApp messages
- Open/Closed: Extensible via MessageBuilder protocol
- Dependency Inversion: Depends on Protocol, not concrete class

DRY Principle:
- ONE implementation for ALL messaging needs
- Uses WAPIClient directly (retry/error handling in client layer)
"""

import logging
from typing import Protocol

import httpx

from clients.wapi.wapi_client import get_wapi_client
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)


class MessageBuilder(Protocol):
    """Protocol for message builders (Dependency Inversion).

    Any callable that takes state and returns string is a valid MessageBuilder.
    This enables:
    - Static templates (lambda s: "Hello!")
    - Dynamic templates (using state data)
    - Jinja2 templates
    - Complex builders with business logic
    """

    def __call__(self, state: BookingState) -> str:
        """Build message text from state.

        Args:
            state: Current booking state

        Returns:
            Message text to send via WhatsApp
        """
        ...


async def node(
    state: BookingState,
    message_builder: MessageBuilder,
    store_in_history: bool = True,
    on_failure: str = "log"
) -> BookingState:
    """Send WhatsApp message using WAPIClient directly.

    Single Responsibility: ONLY sends messages (doesn't extract, validate, transform)

    Uses WAPIClient.send_message() directly - NO call_api wrapper (DRY).

    Args:
        state: Current booking state
        message_builder: ANY function implementing MessageBuilder protocol
        store_in_history: Whether to store message in conversation history
        on_failure: Action on failure - "log" or "raise"

    Returns:
        Updated state with wapi_response and optionally updated history

    Examples:
        # Static template
        await send_message.node(state, lambda s: "Welcome to Yawlit!")

        # Dynamic greeting
        await send_message.node(state, greeting_builder)
    """
    # Build message text
    try:
        message_text = message_builder(state)
        logger.info(f"📤 Building message ({len(message_text)} chars)")

    except Exception as e:
        logger.error(f"❌ Message builder failed: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("message_builder_error")

        if on_failure == "raise":
            raise

        return state

    # Get phone number from conversation_id
    phone_number = state.get("conversation_id", "")

    if not phone_number:
        logger.error("❌ No phone number in conversation_id")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("no_phone_number")
        return state

    # Get WAPI client singleton
    wapi_client = get_wapi_client()

    # Call WAPIClient directly (NO request builder, NO call_api wrapper)
    try:
        logger.info(f"📤 Sending WhatsApp message ({len(message_text)} chars)")

        result = await wapi_client.send_message(
            phone_number=phone_number,
            message_body=message_text
        )

        # Store WAPI response
        state["wapi_response"] = result

        logger.info("✅ WhatsApp message sent successfully")

    except httpx.HTTPError as e:
        logger.error(f"❌ WAPI send failed: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("wapi_send_failed")

        if on_failure == "raise":
            raise

        return state

    except Exception as e:
        logger.error(f"❌ Unexpected error sending message: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("wapi_unexpected_error")

        if on_failure == "raise":
            raise

        return state

    # Store in history if successful
    if store_in_history and "wapi_response" in state:
        # Only store if no errors occurred
        errors = state.get("errors", [])
        if "errors" not in state or "message_send_failed" not in errors:
            if "history" not in state:
                state["history"] = []

            state["history"].append({
                "role": "assistant",
                "content": message_text
            })

            # Also set response field for webhook to use
            state["response"] = message_text

            logger.info("✅ Message sent and stored in history")

    return state
