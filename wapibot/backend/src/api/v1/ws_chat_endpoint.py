"""WebSocket chat endpoint for real-time bidirectional communication.

Provides WebSocket support for frontend chat UI with Redis Streams pub/sub.
HTTP endpoints remain unchanged - this is an addition, not a replacement.
"""

import logging
import json
import uuid
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Query
from starlette.websockets import WebSocketState
import redis.asyncio as aioredis

from core.config import settings
from core.websocket_manager import connection_manager
from workflows.shared.state import BookingState
from workflows.v2_full_workflow import v2_full_workflow

logger = logging.getLogger(__name__)


async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
    token: str = Query(None)  # Optional JWT token for authentication
):
    """WebSocket endpoint for real-time chat.

    Flow:
    1. Accept WebSocket connection
    2. Register in Redis connection registry
    3. Receive messages from client
    4. Process through v2_full_workflow
    5. Publish results to Redis Stream
    6. Redis subscriber forwards to WebSocket connections
    7. Cleanup on disconnect

    Args:
        websocket: FastAPI WebSocket instance
        conversation_id: Conversation/phone number ID
        token: Optional JWT authentication token
    """
    websocket_id = str(uuid.uuid4())
    redis_client: aioredis.Redis = None

    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"📡 WebSocket connection accepted: {websocket_id[:8]}...")

        # TODO: Validate JWT token if provided
        # if token:
        #     user_id = validate_jwt(token)
        # else:
        #     user_id = None

        # Register connection in Redis + SQLite
        await connection_manager.register(
            conversation_id=conversation_id,
            websocket_id=websocket_id,
            websocket=websocket,
            user_id=None  # TODO: Extract from validated token
        )

        # Get Redis client for publishing
        redis_client = await aioredis.from_url(
            settings.celery_broker_url,
            encoding="utf-8",
            decode_responses=True
        )

        # Send connection success message
        await websocket.send_json({
            "type": "connection_established",
            "websocket_id": websocket_id,
            "conversation_id": conversation_id,
            "message": "Connected to WapiBot WebSocket"
        })

        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            user_message = data.get("user_message", "")
            history = data.get("history", [])

            if not user_message.strip():
                logger.debug(f"Skipping empty message from {websocket_id[:8]}...")
                continue

            logger.info(
                f"📥 WebSocket message received: {conversation_id} - "
                f"{user_message[:50]}..."
            )

            # Create BookingState (same as chat_endpoint.py)
            state: BookingState = {
                "conversation_id": conversation_id,
                "user_message": user_message,
                "history": history,
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
            try:
                result = await v2_full_workflow.ainvoke(state)

                # Publish to Redis Stream for delivery
                await redis_client.xadd(
                    settings.redis_stream_name,
                    {
                        "conversation_id": conversation_id,
                        "type": "message",
                        "data": json.dumps({
                            "response": result.get("response", ""),
                            "should_confirm": result.get("should_confirm", False),
                            "completeness": result.get("completeness", 0.0),
                            "extracted_data": {
                                "customer": result.get("customer"),
                                "vehicle": result.get("vehicle"),
                                "appointment": result.get("appointment")
                            }
                        }),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

                logger.info(
                    f"📤 Published to Redis Stream: {conversation_id} - "
                    f"{result.get('response', '')[:50]}..."
                )

            except Exception as e:
                logger.error(
                    f"Workflow execution failed for {websocket_id[:8]}...: {e}",
                    exc_info=True
                )

                # Send error message to client
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to process message. Please try again.",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"📡 WebSocket disconnected (client): {websocket_id[:8]}...")

    except Exception as e:
        logger.error(
            f"WebSocket error for {websocket_id[:8]}...: {e}",
            exc_info=True
        )

    finally:
        # Cleanup: Unregister from Redis + SQLite
        try:
            await connection_manager.unregister(conversation_id, websocket_id)
        except Exception as e:
            logger.error(f"Failed to unregister {websocket_id[:8]}...: {e}")

        # Close WebSocket if still open
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass

        # Close Redis client
        if redis_client:
            try:
                await redis_client.close()
            except Exception:
                pass

        logger.info(f"🔌 WebSocket cleanup complete: {websocket_id[:8]}...")
