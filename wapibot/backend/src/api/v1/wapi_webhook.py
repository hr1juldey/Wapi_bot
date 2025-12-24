"""WAPI webhook endpoint for WhatsApp messages."""

import logging
from fastapi import APIRouter, HTTPException

from schemas.wapi import WAPIWebhookPayload, WAPIResponse
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/wapi", tags=["WAPI"])


@router.post("/webhook", response_model=WAPIResponse)
async def wapi_webhook(payload: WAPIWebhookPayload) -> WAPIResponse:
    """
    Handle incoming WhatsApp messages from WAPI.

    **Flow:**
    1. Validate webhook signature (TODO)
    2. Extract message from WAPI format
    3. Convert to internal BookingState
    4. Run LangGraph workflow
    5. Send response via WAPI API

    **Example Webhook Payload:**
    ```json
    {
      "contact": {
        "phone_number": "919876543210",
        "first_name": "Ravi"
      },
      "message": {
        "whatsapp_message_id": "wamid.abc123",
        "body": "I want to book a car wash"
      }
    }
    ```
    """
    try:
        phone = payload.contact.phone_number
        message_id = payload.message.whatsapp_message_id
        body = payload.message.body or ""

        logger.info(
            f"WAPI webhook: {phone} - {message_id} - {body[:50]}..."
        )

        # TODO: Convert WAPI format to BookingState
        # TODO: Run workflow
        # TODO: Send response via WAPI API

        # For now, acknowledge receipt
        return WAPIResponse(
            status="received",
            message_id=message_id
        )

    except Exception as e:
        logger.error(f"WAPI webhook failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing error: {str(e)}"
        )