"""Atomic QR generation node - ONE node for all QR needs.

DRY Principle: Single node works with ANY amount (default or specified).
Protocol Pattern: Accepts ANY QRGenerator implementation.

Usage:
    await node(state, amount=500)      # With amount
    await node(state, amount=None)     # Any amount option
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, Protocol

from workflows.shared.state import BookingState
from services.qr_service import qr_service
from models.payment_session import PaymentSession, PaymentStatus
from models.payment_transaction import PaymentTransaction, TransactionType
from db.connection import db_connection

logger = logging.getLogger(__name__)


class QRGenerator(Protocol):
    """Protocol for QR generators (extensibility point)."""

    def generate_upi_string(
        self, amount: Optional[float], transaction_note: Optional[str]
    ) -> str:
        """Generate UPI deep link string."""
        ...

    def generate_qr_image(
        self, payment_string: str, session_id: str
    ) -> tuple[bytes, Optional[str]]:
        """Generate QR code PNG image."""
        ...


async def node(
    state: BookingState,
    amount: Optional[float] = None,
    transaction_note: Optional[str] = None,
    generator: QRGenerator = None,
) -> BookingState:
    """Generate UPI QR code - configurable for ANY amount.

    Creates PaymentSession, generates QR, saves to disk, updates state.

    Args:
        state: Current workflow state
        amount: Optional payment amount (None = any amount)
        transaction_note: Optional description for UPI string
        generator: QRGenerator implementation (default: qr_service)

    Returns:
        Updated state with payment_session_id, payment_qr_path, payment_amount
    """
    if generator is None:
        generator = qr_service

    # Generate UPI string
    upi_string = generator.generate_upi_string(amount, transaction_note)
    logger.info(f"📱 Generated UPI string ({len(upi_string)} chars)")

    # Generate QR image
    session_id = str(uuid.uuid4())
    qr_bytes, qr_path = generator.generate_qr_image(upi_string, session_id)
    logger.info(f"🎯 Generated QR code (size={len(qr_bytes)} bytes)")

    # Create database session and save PaymentSession
    async with await db_connection.get_session() as db_session:
        session = PaymentSession(
            session_id=session_id,
            conversation_id=state.get("conversation_id", "unknown"),
            booking_id=state.get("booking_response", {}).get("booking_id"),
            service_request_id=state.get("service_request_id"),
            amount=amount or 0.0,
            upi_string=upi_string,
            qr_image_path=qr_path,
            status=PaymentStatus.PENDING,
            created_at=datetime.now(),
        )
        db_session.add(session)
        await db_session.commit()

        # Log transaction
        transaction = PaymentTransaction(
            session_id=session_id,
            transaction_type=TransactionType.QR_GENERATED,
            amount=amount,
            metadata={"note": transaction_note},
        )
        db_session.add(transaction)
        await db_session.commit()

    # Update state
    state["payment_session_id"] = session_id
    state["payment_qr_path"] = qr_path
    state["payment_amount"] = amount
    state["payment_status"] = PaymentStatus.PENDING.value

    logger.info(
        f"✅ Payment session created: {session_id} "
        f"(amount={amount}, path={qr_path})"
    )

    return state
