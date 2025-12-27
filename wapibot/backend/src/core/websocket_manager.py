"""WebSocket connection manager with Redis-backed registry.

Manages WebSocket connections with Redis for speed and SQLite for persistence.
Designed to handle 200+ concurrent connections with horizontal scalability.
"""

import logging
from datetime import datetime
from typing import Optional

import redis.asyncio as aioredis
from fastapi import WebSocket

from core.config import settings

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """Redis-backed WebSocket connection manager.

    Architecture:
    - Redis Sets: Track websocket_ids per conversation (`connections:{conversation_id}`)
    - Redis Hashes: Store connection metadata (`connection:{websocket_id}`)
    - Redis TTL: Auto-cleanup disconnected connections after 1 hour
    - SQLite: Persistent audit logs for analytics

    Scalability:
    - Supports 200+ concurrent connections via Redis
    - Horizontal scaling (shared state across workers)
    - Message delivery via Redis Streams (handled by redis_subscriber.py)
    """

    def __init__(self):
        """Initialize connection manager."""
        self._redis: Optional[aioredis.Redis] = None
        self._connections: dict[str, WebSocket] = {}  # Local cache: websocket_id -> WebSocket

    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection (lazy initialization)."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.celery_broker_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=250  # Support 200+ concurrent + overhead
            )
            logger.info("✅ Redis connection pool initialized (max 250 connections)")
        return self._redis

    async def register(
        self,
        conversation_id: str,
        websocket_id: str,
        websocket: WebSocket,
        user_id: Optional[str] = None
    ) -> None:
        """Register WebSocket connection in Redis + SQLite.

        Args:
            conversation_id: Conversation/phone number ID
            websocket_id: Unique WebSocket connection ID
            websocket: FastAPI WebSocket instance
            user_id: Optional user identifier
        """
        redis = await self._get_redis()

        # Store WebSocket in local cache (for sending messages)
        self._connections[websocket_id] = websocket

        # Add to Redis Set: connections:{conversation_id}
        await redis.sadd(f"connections:{conversation_id}", websocket_id)

        # Store metadata in Redis Hash: connection:{websocket_id}
        metadata = {
            "conversation_id": conversation_id,
            "user_id": user_id or "",
            "connected_at": datetime.utcnow().isoformat(),
            "messages_sent": "0",
            "messages_received": "0"
        }
        await redis.hset(f"connection:{websocket_id}", mapping=metadata)

        # Set TTL for auto-cleanup (1 hour)
        await redis.expire(f"connection:{websocket_id}", 3600)

        # Log to SQLite for audit (async, non-blocking)
        await self._log_connection_event(
            websocket_id, conversation_id, user_id, "connected"
        )

        logger.info(
            f"📡 WebSocket registered: {websocket_id[:8]}... "
            f"(conversation={conversation_id})"
        )

    async def unregister(self, conversation_id: str, websocket_id: str) -> None:
        """Unregister WebSocket connection from Redis + SQLite.

        Args:
            conversation_id: Conversation ID
            websocket_id: WebSocket connection ID
        """
        redis = await self._get_redis()

        # Remove from local cache
        self._connections.pop(websocket_id, None)

        # Remove from Redis Set
        await redis.srem(f"connections:{conversation_id}", websocket_id)

        # Get final metadata before deletion
        metadata = await redis.hgetall(f"connection:{websocket_id}")

        # Delete metadata Hash
        await redis.delete(f"connection:{websocket_id}")

        # Log to SQLite for audit
        await self._log_connection_event(
            websocket_id,
            conversation_id,
            metadata.get("user_id"),
            "disconnected",
            metadata
        )

        logger.info(
            f"📡 WebSocket unregistered: {websocket_id[:8]}... "
            f"(conversation={conversation_id})"
        )

    async def send_to_conversation(
        self, conversation_id: str, message: dict
    ) -> int:
        """Send message to all WebSockets in a conversation.

        Args:
            conversation_id: Conversation ID to broadcast to
            message: Message dict to send (will be JSON-encoded)

        Returns:
            Number of successful deliveries
        """
        redis = await self._get_redis()

        # Get all websocket_ids for this conversation
        websocket_ids = await redis.smembers(f"connections:{conversation_id}")

        if not websocket_ids:
            logger.debug(f"No active WebSockets for conversation: {conversation_id}")
            return 0

        # Send to each WebSocket
        sent_count = 0
        for websocket_id in websocket_ids:
            websocket = self._connections.get(websocket_id)
            if websocket:
                try:
                    await websocket.send_json(message)

                    # Increment message counter
                    await redis.hincrby(f"connection:{websocket_id}", "messages_sent", 1)
                    sent_count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to send to {websocket_id[:8]}...: {e}"
                    )
                    # Connection broken, will be cleaned up on next heartbeat

        logger.debug(
            f"📤 Sent to {sent_count}/{len(websocket_ids)} WebSockets "
            f"(conversation={conversation_id})"
        )
        return sent_count

    async def broadcast(self, message: dict) -> int:
        """Broadcast message to ALL active WebSocket connections.

        Args:
            message: Message dict to broadcast

        Returns:
            Number of successful deliveries
        """
        sent_count = 0
        for websocket_id, websocket in self._connections.items():
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Broadcast failed to {websocket_id[:8]}...: {e}")

        logger.info(f"📡 Broadcast sent to {sent_count} WebSockets")
        return sent_count

    async def get_connection_count(self, conversation_id: Optional[str] = None) -> int:
        """Get active connection count.

        Args:
            conversation_id: Optional conversation ID (None = total count)

        Returns:
            Number of active connections
        """
        if conversation_id:
            redis = await self._get_redis()
            return await redis.scard(f"connections:{conversation_id}")
        else:
            return len(self._connections)

    async def _log_connection_event(
        self,
        websocket_id: str,
        conversation_id: str,
        user_id: Optional[str],
        event: str,
        metadata: Optional[dict] = None
    ) -> None:
        """Log connection event to SQLite (placeholder for now).

        Will be connected to websocket_db.py once SQLite schema is created.

        Args:
            websocket_id: WebSocket connection ID
            conversation_id: Conversation ID
            user_id: Optional user ID
            event: Event type ('connected', 'disconnected')
            metadata: Optional connection metadata
        """
        # TODO: Connect to SQLite via websocket_db.py (next task)
        logger.debug(
            f"📝 Connection event: {event} (websocket_id={websocket_id[:8]}..., "
            f"conversation={conversation_id})"
        )

    async def close(self) -> None:
        """Close Redis connection and cleanup."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("🔌 Redis connection closed")

        # Clear local cache
        self._connections.clear()


# Global connection manager instance
connection_manager = RedisConnectionManager()
