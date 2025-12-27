"""WebSocket session models for audit logging and analytics.

SQLModel table definition for websocket_sessions.db persistence.
Pydantic schemas for API responses.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class WebSocketSessionTable(SQLModel, table=True):
    """Database table for WebSocket connection audit logs.

    Stores connection lifecycle events for analytics and debugging.
    Separate database (websocket_sessions.db) from main conversations.db.
    """

    __tablename__ = "websocket_sessions"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Auto-incrementing primary key"
    )
    websocket_id: str = Field(
        unique=True,
        index=True,
        description="Unique WebSocket connection ID (UUID)"
    )
    conversation_id: str = Field(
        index=True,
        description="Conversation/phone number ID"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional user identifier"
    )
    connected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Connection establishment timestamp (UTC)"
    )
    disconnected_at: Optional[datetime] = Field(
        default=None,
        description="Connection termination timestamp (UTC)"
    )
    duration_seconds: Optional[int] = Field(
        default=None,
        description="Connection duration in seconds (calculated on disconnect)"
    )
    messages_sent: int = Field(
        default=0,
        description="Number of messages sent to client"
    )
    messages_received: int = Field(
        default=0,
        description="Number of messages received from client"
    )
    disconnect_reason: Optional[str] = Field(
        default=None,
        description="Disconnect reason: client_close, timeout, error, server_shutdown"
    )


# Pydantic schemas for API responses (future use)


class WebSocketSessionResponse(SQLModel):
    """Response schema for WebSocket session data."""

    id: int
    websocket_id: str
    conversation_id: str
    user_id: Optional[str]
    connected_at: datetime
    disconnected_at: Optional[datetime]
    duration_seconds: Optional[int]
    messages_sent: int
    messages_received: int
    disconnect_reason: Optional[str]


class WebSocketSessionStats(SQLModel):
    """Aggregated statistics for WebSocket sessions."""

    total_sessions: int
    active_sessions: int
    avg_duration_seconds: Optional[float]
    total_messages_sent: int
    total_messages_received: int
