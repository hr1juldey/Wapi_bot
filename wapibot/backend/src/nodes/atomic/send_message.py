"""Atomic send message node - works with ANY message builder.

SOLID Principles:
- Single Responsibility: ONLY sends WhatsApp messages
- Open/Closed: Extensible via MessageBuilder protocol
- Dependency Inversion: Depends on Protocol, not concrete class

DRY Principle:
- ONE implementation for ALL messaging needs
- Reuses call_api.node for retry/error/state logic
"""

import logging
from typing import Protocol, Dict, Any
from workflows.shared.state import BookingState
from nodes.atomic.call_api import node as call_api_node
from clients.wapi.wapi_client import get_wapi_client

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
    retry_count: int = 3,
    on_failure: str = "log"
) -> BookingState:
    """Send WhatsApp message using ANY message builder.

    Single Responsibility: ONLY sends messages (doesn't extract, validate, transform)

    Wraps call_api.node internally to reuse retry/error/state logic (DRY).

    Args:
        state: Current booking state
        message_builder: ANY function implementing MessageBuilder protocol
        store_in_history: Whether to store message in conversation history
        retry_count: Number of retry attempts (delegated to call_api)
        on_failure: Action on failure - "log" or "raise"

    Returns:
        Updated state with wapi_response and optionally updated history

    Examples:
        # Static template
        await send_message.node(state, lambda s: "Welcome to Yawlit!")

        # Dynamic greeting
        await send_message.node(state, greeting_builder)

        # All use SAME node - DRY!
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

    # Create WAPI request builder (wraps WAPI endpoint)
    wapi_client = get_wapi_client()

    def wapi_send_request_builder(s: BookingState) -> Dict[str, Any]:
        """Build WAPI send-message request.

        This is a RequestBuilder that call_api.node understands.
        """
        return {
            "method": "POST",
            "url": f"{wapi_client.base_url}/{wapi_client.vendor_uid}/contact/send-message",
            "headers": {
                "Authorization": f"Bearer {wapi_client.bearer_token}",
                "Content-Type": "application/json"
            },
            "json": {
                "phone_number": phone_number,
                "message_body": message_text,
                "from_phone_number_id": wapi_client.from_phone_number_id
            }
        }

    # Delegate to call_api.node (reuses ALL retry/error/state logic - DRY!)
    state = await call_api_node(
        state,
        wapi_send_request_builder,
        "wapi_response",
        retry_count=retry_count,
        on_failure=on_failure
    )

    # Store in history if successful
    if store_in_history and "wapi_response" in state:
        # Only store if no errors occurred
        if "errors" not in state or "message_send_failed" not in state.get("errors", []):
            if "history" not in state:
                state["history"] = []

            state["history"].append({
                "role": "assistant",
                "content": message_text
            })

            logger.info("✅ Message sent and stored in history")

    return state
