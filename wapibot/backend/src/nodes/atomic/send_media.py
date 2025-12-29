"""Atomic media message node for WAPI.

Sends media messages (images, videos, documents) via WhatsApp Business API.
Protocol-based design allows ANY media builder implementation.
"""

import logging
from typing import Protocol, Dict, Any
from workflows.shared.state import BookingState
from clients.wapi import get_wapi_client

logger = logging.getLogger(__name__)


class MediaBuilder(Protocol):
    """Protocol for media message builders.

    Allows flexible media message construction for ANY use case.
    """

    def __call__(self, state: BookingState) -> Dict[str, Any]:
        """Build media message parameters from state.

        Returns:
            Dictionary with keys:
                - media_type: "image", "video", or "document"
                - media_url: Publicly accessible HTTPS URL
                - caption: Optional caption for image/video
                - file_name: Optional file name for document
        """
        ...


async def node(
    state: BookingState,
    media_builder: MediaBuilder,
) -> BookingState:
    """Send media message via WAPI.

    Follows atomic node pattern: accepts Protocol, logs extensively,
    returns updated state with response.

    Args:
        state: Current workflow state
        media_builder: Protocol that builds media parameters

    Returns:
        Updated state with wapi_response and message metadata
    """
    client = get_wapi_client()

    # Build media parameters from state
    media_params = media_builder(state)

    # Extract required fields
    media_type = media_params.get("media_type")
    media_url = media_params.get("media_url")
    caption = media_params.get("caption")
    file_name = media_params.get("file_name")

    # Get phone number from state
    phone_number = state.get("customer", {}).get("phone")

    if not phone_number:
        logger.error("❌ No phone number in state")
        state["wapi_error"] = "No phone number in state"
        return state

    # Ensure country code (WAPI requires full international format)
    # Frappe returns "6290818033", WAPI needs "916290818033"
    if not phone_number.startswith("91") and len(phone_number) == 10:
        phone_number = f"91{phone_number}"
        logger.info(f"📱 Added country code: 91{phone_number[-10:]}")

    logger.info(
        f"📸 Sending {media_type} to {phone_number}: {media_url[:50]}..."
    )

    try:
        result = await client.send_media(
            phone_number=phone_number,
            media_type=media_type,
            media_url=media_url,
            caption=caption,
            file_name=file_name,
        )

        logger.info(f"✅ Media sent successfully to {phone_number}")
        state["wapi_response"] = result
        state["message_sent"] = True

        return state

    except Exception as e:
        logger.error(f"❌ Failed to send media to {phone_number}: {e}")
        state["wapi_error"] = str(e)
        state["message_sent"] = False
        raise
