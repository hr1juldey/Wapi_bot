"""WAPI webhook endpoint for WhatsApp messages."""

import logging
import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional

from core.config import settings
from schemas.wapi import WAPIWebhookPayload, WAPIResponse
from schemas.chat import ChatRequest
from workflows.shared.state import BookingState
from workflows.v2_full_workflow import v2_full_workflow
from clients.wapi import get_wapi_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/wapi", tags=["WAPI"])


def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """Verify WAPI webhook signature using HMAC-SHA256.

    Args:
        payload_body: Raw request body bytes
        signature: Signature from X-WAPI-Signature header

    Returns:
        True if signature is valid, False otherwise
    """
    if not settings.wapi_webhook_secret:
        logger.warning("WAPI webhook secret not configured - skipping signature verification")
        return True  # Allow in development when secret not set

    if not signature:
        return False

    # Compute HMAC-SHA256 signature
    expected_signature = hmac.new(
        settings.wapi_webhook_secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


@router.post("/webhook", response_model=WAPIResponse)
async def wapi_webhook(
    request: Request,
    payload: WAPIWebhookPayload,
    x_wapi_signature: Optional[str] = Header(None, alias="X-WAPI-Signature")
) -> WAPIResponse:
    """
    Handle incoming WhatsApp messages from WAPI with signature validation.

    **Security:**
    - Validates HMAC-SHA256 signature from X-WAPI-Signature header
    - Rejects requests with invalid or missing signatures (in production)

    **Flow:**
    1. Validate webhook signature using HMAC-SHA256
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

    **Headers:**
    - X-WAPI-Signature: HMAC-SHA256 signature of request body
    """
    try:
        # Security: Verify webhook signature
        raw_body = await request.body()
        if not verify_webhook_signature(raw_body, x_wapi_signature or ""):
            logger.warning(f"Invalid webhook signature from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )

        phone = payload.contact.phone_number
        message_id = payload.message.whatsapp_message_id
        body = payload.message.body or ""

        logger.info(
            f"WAPI webhook: {phone} - {message_id} - {body[:50]}..."
        )

        # Skip processing if not a new message
        if not payload.message.is_new_message:
            logger.debug(f"Skipping non-new message: {message_id}")
            return WAPIResponse(status="skipped", message_id=message_id)

        # Skip empty messages
        if not body.strip():
            logger.debug(f"Skipping empty message: {message_id}")
            return WAPIResponse(status="skipped", message_id=message_id)

        # Create initial state for workflow
        state: BookingState = {
            "conversation_id": phone,
            "user_message": body,
            "history": [],  # TODO: Load from database
            "customer": None,
            "vehicle": None,
            "appointment": None,
            "sentiment": None,
            "intent": None,
            "intent_confidence": 0.0,
            "current_step": "extract_name",
            "completeness": 0.0,
            "errors": [],
            "response": "",
            "should_confirm": False,
            "should_proceed": True,
            "service_request_id": None,
            "service_request": None
        }

        # Run V2 full workflow
        logger.info(f"Processing message through workflow: {phone}")
        result = await v2_full_workflow.ainvoke(state)

        # Extract response message
        response_message = result.get("response", "")

        if not response_message:
            logger.warning(f"Workflow produced no response for {phone}")
            response_message = "I'm processing your request. Please wait a moment."

        # Send response via WAPI
        wapi_client = get_wapi_client()

        try:
            # Build contact data for auto-creation
            contact_data = {
                "first_name": payload.contact.first_name or "Customer",
                "last_name": payload.contact.last_name or "",
                "email": payload.contact.email or "",
                "country": payload.contact.country or "india",
                "language_code": payload.contact.language_code or "en"
            }

            await wapi_client.send_message(
                phone_number=phone,
                message_body=response_message,
                contact=contact_data
            )

            logger.info(f"Response sent to {phone}: {response_message[:50]}...")

        except Exception as e:
            logger.error(f"Failed to send WAPI response to {phone}: {e}", exc_info=True)
            # Don't fail the webhook - message was processed
            # WAPI will retry if needed

        # Acknowledge receipt
        return WAPIResponse(
            status="received",
            message_id=message_id
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 401 signature validation failure)
        raise
    except Exception as e:
        logger.error(f"WAPI webhook failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred during webhook processing"
        )