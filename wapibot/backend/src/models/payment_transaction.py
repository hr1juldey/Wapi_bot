"""Payment transaction audit log model.

Immutable record of all payment-related events for audit trail.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from sqlmodel import Field, SQLModel, JSON, Column


class TransactionType(str, Enum):
    """Types of payment transactions."""

    QR_GENERATED = "qr_generated"
    REMINDER_SENT = "reminder_sent"
    ADMIN_CONFIRMED = "admin_confirmed"
    AUTO_EXPIRED = "auto_expired"
    PAYMENT_FAILED = "payment_failed"


class PaymentTransaction(SQLModel, table=True):
    """Immutable audit log of payment events.

    Every payment action (QR generated, reminder sent, admin confirmed)
    creates one transaction record. Never modified, only appended.
    """

    __tablename__ = "payment_transactions"

    # Primary key (auto-increment)
    transaction_id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to payment session
    session_id: str = Field(
        foreign_key="payment_sessions.session_id", index=True
    )

    # Transaction type
    transaction_type: TransactionType = Field(
        index=True, description="Type of payment event"
    )

    # Optional amount for confirmation transactions
    amount: Optional[float] = Field(default=None)

    # Flexible metadata (JSON)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Event-specific metadata (reminder_number, admin_user, etc.)",
    )

    # Timestamp
    created_at: datetime = Field(
        default_factory=datetime.now, index=True, description="When event occurred"
    )
