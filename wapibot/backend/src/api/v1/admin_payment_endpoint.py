"""Admin payment confirmation API endpoint.

Allows admin to manually confirm that payment was received.
Cancels pending reminders when payment confirmed.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import select

from db.connection import db_connection
from models import PaymentSession, PaymentStatus, PaymentTransaction, TransactionType
from tasks.payment_tasks import cancel_pending_reminders

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/payments", tags=["admin", "payments"])


class PaymentConfirmationRequest(BaseModel):
    """Request model for payment confirmation."""

    session_id: str = Field(..., description="Payment session UUID")
    admin_user: str = Field(..., description="Admin email confirming payment")
    payment_proof: str = Field(
        default=None, description="Reference number or proof of payment"
    )
    notes: str = Field(default=None, description="Optional admin notes")


class PaymentConfirmationResponse(BaseModel):
    """Response model for payment confirmation."""

    session_id: str
    status: str
    message: str
    confirmed_at: str
    confirmed_by: str


@router.post(
    "/confirm",
    response_model=PaymentConfirmationResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_payment(
    request: PaymentConfirmationRequest,
) -> PaymentConfirmationResponse:
    """Confirm payment received by admin.

    Marks PaymentSession as CONFIRMED, logs transaction, and cancels
    pending reminder tasks.

    Args:
        request: Confirmation request with session_id and admin details

    Returns:
        Confirmation response with updated payment status

    Raises:
        HTTPException: If session not found or already confirmed
    """
    async with await db_connection.get_session() as db_session:
        # Fetch PaymentSession
        result = await db_session.execute(
            select(PaymentSession).where(
                PaymentSession.session_id == request.session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            logger.error(f"❌ Payment session not found: {request.session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment session not found",
            )

        if session.status == PaymentStatus.CONFIRMED:
            logger.warning(f"⚠️ Payment already confirmed: {request.session_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment already confirmed",
            )

        # Update PaymentSession
        session.status = PaymentStatus.CONFIRMED
        session.confirmed_at = datetime.now()
        session.confirmed_by = request.admin_user
        db_session.add(session)

        # Log transaction
        transaction = PaymentTransaction(
            session_id=request.session_id,
            transaction_type=TransactionType.ADMIN_CONFIRMED,
            amount=session.amount,
            metadata={
                "admin_user": request.admin_user,
                "payment_proof": request.payment_proof,
                "notes": request.notes,
            },
        )
        db_session.add(transaction)

        await db_session.commit()

        logger.info(
            f"✅ Payment confirmed by {request.admin_user} "
            f"(session={request.session_id})"
        )

        # Cancel pending reminders asynchronously
        cancel_pending_reminders.delay(request.session_id)

        return PaymentConfirmationResponse(
            session_id=request.session_id,
            status="confirmed",
            message="Payment confirmed successfully",
            confirmed_at=session.confirmed_at.isoformat(),
            confirmed_by=request.admin_user,
        )


@router.get("/status/{session_id}")
async def get_payment_status(session_id: str) -> dict:
    """Get payment status for a session.

    Args:
        session_id: Payment session UUID

    Returns:
        Payment status details

    Raises:
        HTTPException: If session not found
    """
    async with await db_connection.get_session() as db_session:
        result = await db_session.execute(
            select(PaymentSession).where(
                PaymentSession.session_id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment session not found",
            )

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "amount": session.amount,
            "created_at": session.created_at.isoformat(),
            "confirmed_at": session.confirmed_at.isoformat()
            if session.confirmed_at
            else None,
            "confirmed_by": session.confirmed_by,
            "reminder_count": session.reminder_count,
        }
