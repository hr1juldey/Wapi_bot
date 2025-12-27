"""Redis Streams subscriber for WebSocket message delivery.

Consumes messages from Redis Streams and forwards to WebSocket connections.
Provides delivery guarantees via consumer groups and acknowledgment.
"""

import asyncio
import logging
import json
from typing import Optional

import redis.asyncio as aioredis

from core.config import settings
from core.websocket_manager import connection_manager

logger = logging.getLogger(__name__)


class RedisSubscriber:
    """Redis Streams consumer for WebSocket message delivery.

    Architecture:
    - Stream: `chat_messages` (persistent message queue)
    - Consumer Group: `websocket_workers` (load balancing across workers)
    - Consumer Name: `worker-{uuid}` (unique per instance)
    - Acknowledgment: XACK after successful delivery

    Delivery Guarantees:
    - Messages persist in stream even if no consumers active
    - Consumer group tracks which messages each consumer processed
    - Failed deliveries can be retried by other consumers
    """

    def __init__(self):
        """Initialize Redis subscriber."""
        self._redis: Optional[aioredis.Redis] = None
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._consumer_name: str = f"worker-{id(self)}"

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection (lazy initialization)."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.celery_broker_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("✅ Redis subscriber connected")
        return self._redis

    async def _ensure_stream_and_group(self) -> None:
        """Ensure stream and consumer group exist."""
        redis = await self._get_redis()

        try:
            # Try to create consumer group
            await redis.xgroup_create(
                name=settings.redis_stream_name,
                groupname=settings.redis_consumer_group,
                id="0",  # Start from beginning
                mkstream=True  # Create stream if doesn't exist
            )
            logger.info(
                f"✅ Created consumer group: {settings.redis_consumer_group} "
                f"on stream: {settings.redis_stream_name}"
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Consumer group already exists
                logger.debug(
                    f"Consumer group already exists: {settings.redis_consumer_group}"
                )
            else:
                raise

    async def _process_message(
        self, message_id: str, message_data: dict
    ) -> bool:
        """Process a single message from the stream.

        Args:
            message_id: Redis Stream message ID
            message_data: Message payload

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            conversation_id = message_data.get("conversation_id")
            message_type = message_data.get("type", "message")
            data = message_data.get("data")

            if not conversation_id:
                logger.warning(f"Message missing conversation_id: {message_id}")
                return False

            # Parse JSON data if present
            if data:
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in message data: {message_id}")
                    return False

            # Forward to WebSocket connections
            payload = {
                "type": message_type,
                "conversation_id": conversation_id,
                "data": data,
                "timestamp": message_data.get("timestamp")
            }

            sent_count = await connection_manager.send_to_conversation(
                conversation_id, payload
            )

            if sent_count > 0:
                logger.debug(
                    f"✅ Delivered message {message_id[:8]}... to {sent_count} WebSocket(s)"
                )
            else:
                logger.debug(
                    f"⚠️ No active WebSockets for conversation: {conversation_id}"
                )

            return True

        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}", exc_info=True)
            return False

    async def _consume_loop(self) -> None:
        """Main consumption loop (runs in background)."""
        redis = await self._get_redis()

        logger.info(
            f"🔄 Starting Redis Streams consumer: {self._consumer_name} "
            f"(group={settings.redis_consumer_group})"
        )

        while self._running:
            try:
                # Read messages from stream
                # XREADGROUP: block for 1 second, read max 10 messages
                messages = await redis.xreadgroup(
                    groupname=settings.redis_consumer_group,
                    consumername=self._consumer_name,
                    streams={settings.redis_stream_name: ">"},
                    count=10,
                    block=1000  # Block for 1 second
                )

                if not messages:
                    # No new messages, continue
                    continue

                # Process each message
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        success = await self._process_message(message_id, message_data)

                        if success:
                            # Acknowledge message
                            await redis.xack(
                                settings.redis_stream_name,
                                settings.redis_consumer_group,
                                message_id
                            )
                        else:
                            logger.warning(
                                f"Failed to process message {message_id}, "
                                f"will be retried by another consumer"
                            )

            except asyncio.CancelledError:
                logger.info("Consumer loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}", exc_info=True)
                # Brief backoff before retry
                await asyncio.sleep(1)

        logger.info(f"🛑 Redis Streams consumer stopped: {self._consumer_name}")

    async def start(self) -> None:
        """Start the Redis Streams consumer background task."""
        if self._running:
            logger.warning("Redis subscriber already running")
            return

        # Ensure stream and consumer group exist
        await self._ensure_stream_and_group()

        # Start background consumption loop
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())

        logger.info("✅ Redis Streams subscriber started")

    async def stop(self) -> None:
        """Stop the Redis Streams consumer."""
        if not self._running:
            return

        self._running = False

        # Cancel background task
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        # Close Redis connection
        if self._redis:
            await self._redis.close()
            self._redis = None

        logger.info("✅ Redis Streams subscriber stopped")


# Global subscriber instance
redis_subscriber = RedisSubscriber()
