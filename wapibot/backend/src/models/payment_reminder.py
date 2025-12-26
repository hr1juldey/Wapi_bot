"""Payment reminder tracking model.

Tracks scheduled reminders, execution status, and failure reasons.
Enables cancellation of pending reminders when payment confirmed.
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlmodel import Field, SQLModel


class ReminderStatus(str, Enum):
    """Status of a scheduled reminder."""

    SCHEDULED = "scheduled"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentReminder(SQLModel, table=True):
    """Scheduled payment reminder.

    Tracks when reminders should be sent, execution status,
    and Celery task ID for cancellation.
    """

    __tablename__ = "payment_reminders"

    # Primary key (auto-increment)
    reminder_id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to payment session
    session_id: str = Field(
        foreign_key="payment_sessions.session_id", index=True
    )

    # Reminder sequence number
    reminder_number: int = Field(
        description="0=instant (when QR sent), 1=first scheduled, 2=second, etc."
    )

    # Scheduling
    scheduled_at: datetime = Field(
        index=True, description="When this reminder is scheduled to be sent"
    )

    # Status
    status: ReminderStatus = Field(
        default=ReminderStatus.SCHEDULED, index=True, description="Current status"
    )

    # Celery task tracking
    celery_task_id: Optional[str] = Field(
        default=None,
        description="Celery task ID for cancellation when payment confirmed",
    )

    # Execution tracking
    sent_at: Optional[datetime] = Field(
        default=None, description="When reminder was actually sent"
    )

    error_message: Optional[str] = Field(
        default=None, description="Error reason if status=FAILED"
    )
