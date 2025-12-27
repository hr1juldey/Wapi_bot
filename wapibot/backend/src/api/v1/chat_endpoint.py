"""V2 Full chat endpoint demonstrating atomic node composition.

This endpoint uses the full V2 workflow with:
- Extract → Confidence check → Scan → Merge → Response
- Demonstrates all atomic nodes working together
"""

import logging
from fastapi import APIRouter, HTTPException

from models.chat_schemas import ChatRequest, ChatResponse
from workflows.shared.state import BookingState
from workflows.v2_full_workflow import v2_full_workflow

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Process chat message using V2 atomic node workflow.

    This endpoint demonstrates the full V2 architecture:
    - Atomic extract node with DSPy
    - Confidence-based routing
    - Retroactive scanning (V1's strength)
    - Confidence-based merging (fixes V1's bug)

    **Flow:**
    1. Extract name (atomic extract node)
    2. Check confidence (atomic confidence_gate node)
    3. If low: scan history (atomic scan node) → merge (atomic merge node)
    4. If high: proceed directly to response
    5. Generate response

    **Example Request:**
    ```json
    {
      "conversation_id": "919876543210",
      "user_message": "Hi, I am Hrijul Dey",
      "history": []
    }
    ```

    **Example Response:**
    ```json
    {
      "message": "Nice to meet you, Hrijul! 👋",
      "should_confirm": false,
      "completeness": 0.3,
      "extracted_data": {
        "customer": {
          "first_name": "Hrijul",
          "last_name": "Dey",
          "confidence": 0.9,
          "extraction_method": "dspy"
        }
      }
    }
    ```

    **Edge Case Example (low confidence → retroactive scan):**
    ```json
    {
      "conversation_id": "919876543210",
      "user_message": "Yes, I want to book",
      "history": [
        {"role": "user", "content": "Hi, I am Hrijul"},
        {"role": "assistant", "content": "Hello! How can I help?"}
      ]
    }
    ```

    Response:
    ```json
    {
      "message": "Nice to meet you, Hrijul! 👋 (I found your name from our earlier conversation)",
      "completeness": 0.3,
      "extracted_data": {
        "customer": {
          "first_name": "Hrijul",
          "confidence": 0.8,
          "extraction_method": "retroactive_scan"
        }
      }
    }
    ```
    """
    try:
        # Extract fields from either format
        conversation_id = request.get_conversation_id()
        user_message = request.get_user_message()

        logger.info(
            f"Processing chat: {conversation_id} - "
            f"{user_message[:50]}..."
        )

        # Log which format was used
        if request.contact:
            logger.info("[Chat] Using WAPI-like format (frontend testing mode)")
        else:
            logger.info("[Chat] Using simple format")

        # Create initial state
        state: BookingState = {
            "conversation_id": conversation_id,
            "user_message": user_message,
            "history": request.history or [],
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

        # Run V2 full workflow (atomic nodes composition)
        result = await v2_full_workflow.ainvoke(state)

        # Build response
        response = ChatResponse(
            message=result.get("response", "Processing complete!"),
            should_confirm=result.get("should_confirm", False),
            completeness=result.get("completeness", 0.0),
            extracted_data={
                "customer": result.get("customer"),
                "vehicle": result.get("vehicle"),
                "appointment": result.get("appointment")
            },
            service_request_id=result.get("service_request_id")
        )

        logger.info(f"Response: {response.message[:50]}...")
        logger.info(f"Extracted: {result.get('customer')}")

        return response

    except Exception as e:
        logger.error(f"Chat processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred during chat processing"
        )
