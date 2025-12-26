"""Atomic payment status check node.

Checks if admin has confirmed payment for a session.
Updates state with payment confirmation status.
"""

import logging

from workflows.shared.state import BookingState
from models.payment_session import PaymentStatus
from db.connection import db_connection

logger = logging.getLogger(__name__)


async def node(state: BookingState) -> BookingState:
    """Check payment confirmation status.

    Fetches PaymentSession and checks if status=CONFIRMED.
    Updates state with confirmation status and details.

    Args:
        state: Current workflow state

    Returns:
        Updated state with payment_confirmed flag and details
    """
    session_id = state.get("payment_session_id")

    if not session_id:
        logger.warning("⚠️ No payment_session_id - payment not confirmed")
        state["payment_confirmed"] = False
        return state

    try:
        async with await db_connection.get_session() as db_session:
            from sqlmodel import select
            from models import PaymentSession

            # Fetch PaymentSession
            result = await db_session.execute(
                select(PaymentSession).where(
                    PaymentSession.session_id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session:
                logger.warning(f"❌ Session not found: {session_id}")
                state["payment_confirmed"] = False
                return state

            # Check confirmation status
            is_confirmed = session.status == PaymentStatus.CONFIRMED
            state["payment_confirmed"] = is_confirmed
            state["payment_status"] = session.status.value

            if is_confirmed:
                state["payment_confirmed_at"] = session.confirmed_at.isoformat()
                state["payment_confirmed_by"] = session.confirmed_by
                logger.info(f"✅ Payment confirmed by {session.confirmed_by}")
            else:
                logger.info(f"⏳ Payment pending (status={session.status.value})")

    except Exception as e:
        logger.error(f"❌ Failed to check payment status: {e}")
        state["payment_confirmed"] = False

        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("payment_status_check_failed")

    return state
