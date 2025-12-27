"""Admin payment API request/response schemas.

Extracted from admin_payment_endpoint.py to comply with 100-line limit.
Follows SOLID Single Responsibility Principle - schemas separate from routing.
"""

from pydantic import BaseModel, Field
from schemas.examples import (
    EXAMPLE_SESSION_UUID,
    EXAMPLE_SESSION_UUID_ALT,
    EXAMPLE_SESSION_UUID_THIRD,
    EXAMPLE_ADMIN_EMAIL,
    EXAMPLE_ADMIN_EMAIL_ALT,
    EXAMPLE_UTR_NUMBER,
    EXAMPLE_UTR_NUMBER_ALT,
    EXAMPLE_PAYMENT_AMOUNT_HATCHBACK,
    EXAMPLE_PAYMENT_AMOUNT_SUV,
    EXAMPLE_TIMESTAMP_CREATED,
    EXAMPLE_TIMESTAMP_CONFIRMED,
)


class PaymentConfirmationRequest(BaseModel):
    """Request to confirm payment received by admin."""

    session_id: str = Field(
        ...,
        description="Payment session UUID",
        examples=[EXAMPLE_SESSION_UUID]
    )
    admin_user: str = Field(
        ...,
        description="Admin email confirming payment",
        examples=[EXAMPLE_ADMIN_EMAIL]
    )
    payment_proof: str = Field(
        default=None,
        description="UTR or transaction reference number",
        examples=[EXAMPLE_UTR_NUMBER]
    )
    notes: str = Field(
        default=None,
        description="Optional admin notes about payment verification",
        examples=["Verified via bank statement"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": EXAMPLE_SESSION_UUID,
                "admin_user": EXAMPLE_ADMIN_EMAIL,
                "payment_proof": EXAMPLE_UTR_NUMBER,
                "notes": "Payment verified via bank statement"
            }
        }


class PaymentConfirmationResponse(BaseModel):
    """Response after payment confirmation."""

    session_id: str = Field(
        ...,
        description="Payment session UUID",
        examples=[EXAMPLE_SESSION_UUID]
    )
    status: str = Field(
        ...,
        description="Payment status after confirmation",
        examples=["confirmed"]
    )
    message: str = Field(
        ...,
        description="Human-readable confirmation message",
        examples=["Payment confirmed successfully"]
    )
    confirmed_at: str = Field(
        ...,
        description="ISO timestamp of confirmation",
        examples=[EXAMPLE_TIMESTAMP_CONFIRMED]
    )
    confirmed_by: str = Field(
        ...,
        description="Admin email who confirmed payment",
        examples=[EXAMPLE_ADMIN_EMAIL]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": EXAMPLE_SESSION_UUID,
                "status": "confirmed",
                "message": "Payment confirmed successfully",
                "confirmed_at": EXAMPLE_TIMESTAMP_CONFIRMED,
                "confirmed_by": EXAMPLE_ADMIN_EMAIL
            }
        }


class PaymentStatusResponse(BaseModel):
    """Response for payment status query."""

    session_id: str = Field(
        ...,
        description="Payment session UUID",
        examples=[EXAMPLE_SESSION_UUID]
    )
    status: str = Field(
        ...,
        description="Current payment status",
        examples=["pending", "confirmed", "expired", "cancelled"]
    )
    amount: float = Field(
        ...,
        description="Payment amount in INR",
        examples=[EXAMPLE_PAYMENT_AMOUNT_HATCHBACK, EXAMPLE_PAYMENT_AMOUNT_SUV]
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp when payment session created",
        examples=[EXAMPLE_TIMESTAMP_CREATED]
    )
    confirmed_at: str | None = Field(
        ...,
        description="ISO timestamp when payment confirmed (null if pending)",
        examples=[EXAMPLE_TIMESTAMP_CONFIRMED, None]
    )
    confirmed_by: str | None = Field(
        ...,
        description="Admin email who confirmed (null if pending)",
        examples=[EXAMPLE_ADMIN_EMAIL, None]
    )
    reminder_count: int = Field(
        ...,
        description="Number of payment reminders sent",
        examples=[0, 1, 2, 3]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": EXAMPLE_SESSION_UUID,
                "status": "confirmed",
                "amount": EXAMPLE_PAYMENT_AMOUNT_HATCHBACK,
                "created_at": EXAMPLE_TIMESTAMP_CREATED,
                "confirmed_at": EXAMPLE_TIMESTAMP_CONFIRMED,
                "confirmed_by": EXAMPLE_ADMIN_EMAIL,
                "reminder_count": 0
            }
        }
