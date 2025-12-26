"""Payment session tracking model.

Tracks UPI QR code lifecycle, confirmation status, and reminder history.
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlmodel import Field, SQLModel


class PaymentStatus(str, Enum):
    """Payment session status values."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PaymentSession(SQLModel, table=True):
    """Single payment session linked to a booking.

    Tracks:
    - QR code generation and location
    - Payment confirmation status
    - Admin confirmation details
    - Reminder history metadata
    """

    __tablename__ = "payment_sessions"

    # Primary key
    session_id: str = Field(primary_key=True, index=True)

    # Relationships
    conversation_id: str = Field(index=True)
    booking_id: Optional[str] = Field(default=None, index=True)
    service_request_id: Optional[str] = None

    # Payment details
    amount: float = Field(description="Payment amount in rupees")
    upi_string: str = Field(description="UPI deep link: upi://pay?pa=...")
    qr_image_path: Optional[str] = Field(
        default=None, description="Path to saved QR code PNG file"
    )

    # Status tracking
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING, index=True, description="Current payment status"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now, index=True, description="When QR was generated"
    )
    confirmed_at: Optional[datetime] = Field(
        default=None, description="When payment was confirmed"
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="When payment request expires (7 days default)"
    )

    # Reminder metadata
    reminder_count: int = Field(default=0, description="Number of reminders sent")
    last_reminder_at: Optional[datetime] = Field(
        default=None, description="Timestamp of last reminder sent"
    )

    # Confirmation metadata
    confirmed_by: Optional[str] = Field(
        default=None, description="Admin email who confirmed payment"
    )
