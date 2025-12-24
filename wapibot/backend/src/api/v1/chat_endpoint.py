"""Chat endpoint for frontend/testing."""

import logging
from fastapi import APIRouter, HTTPException

from schemas.chat import ChatRequest, ChatResponse
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Process chat message and extract booking data.

    **Flow:**
    1. Create BookingState from request
    2. Run LangGraph workflow (TODO: implement)
    3. Return response with extracted data

    **Example Request:**
    ```json
    {
      "conversation_id": "919876543210",
      "user_message": "I want to book a car wash for my Honda City tomorrow"
    }
    ```

    **Example Response:**
    ```json
    {
      "message": "Great! I can help you. What's your name?",
      "should_confirm": false,
      "completeness": 0.3,
      "extracted_data": {
        "vehicle": {"brand": "Honda", "model": "City"}
      }
    }
    ```
    """
    try:
        logger.info(
            f"Processing chat: {request.conversation_id} - "
            f"{request.user_message[:50]}..."
        )

        # TODO: Create BookingState and run workflow
        # For now, return mock response
        response = ChatResponse(
            message=f"Received your message: '{request.user_message}'. "
                    "Workflow processing coming soon!",
            should_confirm=False,
            completeness=0.0,
            extracted_data={
                "customer": None,
                "vehicle": None,
                "appointment": None
            },
            service_request_id=None
        )

        logger.info(f"Response: {response.message[:50]}...")
        return response

    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing error: {str(e)}"
        )