"""WAPI webhook endpoint for WhatsApp messages."""

import logging
import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional

from core.config import settings
from schemas.wapi import WAPIWebhookPayload, WAPIResponse
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/wapi", tags=["WAPI"])


def get_active_workflow():
    """Dynamically load the active workflow based on settings.

    This allows hot-swapping workflows by just changing ACTIVE_WORKFLOW in .env.txt
    and restarting the server - no code changes needed!

    Returns:
        Compiled LangGraph workflow

    Raises:
        ValueError: If workflow name is not recognized
    """
    workflow_name = settings.active_workflow

    logger.info(f"Loading workflow: {workflow_name}")

    if workflow_name == "existing_user_booking":
        from workflows.existing_user_booking import create_existing_user_booking_workflow
        return create_existing_user_booking_workflow()

    elif workflow_name == "marketing_to_registration":
        from workflows.marketing_to_registration import create_marketing_to_registration_workflow
        return create_marketing_to_registration_workflow()

    elif workflow_name == "v2_full_workflow":
        from workflows.v2_full_workflow import v2_full_workflow
        return v2_full_workflow

    else:
        raise ValueError(
            f"Unknown workflow: {workflow_name}. "
            f"Valid options: existing_user_booking, marketing_to_registration, v2_full_workflow"
        )


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

        # Get workflow and config for state persistence
        logger.info(f"Processing message through {settings.active_workflow} workflow: {phone}")
        workflow = get_active_workflow()
        config = {"configurable": {"thread_id": phone}}

        # Try to load existing state from checkpointer
        last_state = None
        try:
            state_snapshot = await workflow.aget_state(config)
            if state_snapshot and state_snapshot.values:
                last_state = state_snapshot.values
                logger.info(f"Loaded existing state for {phone}")
        except Exception as e:
            logger.debug(f"No existing state for {phone}: {e}")

        # Create or update state
        if last_state:
            # Resume conversation - update user_message
            state: BookingState = dict(last_state)
            state["user_message"] = body
            logger.info(f"Resuming conversation for {phone}")
        else:
            # New conversation - initialize state
            state: BookingState = {
                "conversation_id": phone,
                "user_message": body,
                "history": [],
                "customer": None,
                "vehicle": None,
                "vehicle_options": None,
                "vehicle_selected": False,
                "vehicles_response": None,
                "appointment": None,
                "sentiment": None,
                "intent": None,
                "intent_confidence": 0.0,
                "current_step": "entry_router",
                "completeness": 0.0,
                "errors": [],
                "response": "",
                "should_confirm": False,
                "should_proceed": True,
                "service_request_id": None,
                "service_request": None,
                "customer_lookup_response": None,
                "services_response": None,
                "wapi_response": None,
                "filtered_services": None,
                "selected_service": None,
                "service_selected": False,
                "selection_error": None,
                "available_slots": None,
                "formatted_slots": None,
                "slot_selected": False,
                "total_price": None,
                "confirmed": None,
                "gate_decision": None,
            }
            logger.info(f"Starting new conversation for {phone}")

        # Run workflow with config for checkpointing
        result = await workflow.ainvoke(state, config=config)

        # Check if workflow already sent messages (via send_message_node)
        # send_message_node sends directly via WAPI, so no need to send again
        response_message = result.get("response", "")

        if response_message:
            logger.info(f"Workflow sent response to {phone}: {response_message[:50]}...")
            logger.info("✅ Message already sent by workflow (via send_message_node)")
        else:
            logger.warning(f"Workflow produced no response for {phone}")
            logger.info("No message sent - workflow may have ended without response")

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