"""Atomic reminder scheduling node - NON-BLOCKING.

Schedules Celery tasks for payment reminders.
Non-blocking: workflow continues even if scheduling fails.

Protocol Pattern: Accepts ANY ReminderScheduler implementation.
"""

import logging
from typing import Optional, Protocol

from workflows.shared.state import BookingState
from services.reminder_service import reminder_service
from models.payment_session import PaymentSession
from db.connection import db_connection

logger = logging.getLogger(__name__)


class ReminderScheduler(Protocol):
    """Protocol for reminder schedulers (extensibility point)."""

    async def schedule_reminders(
        self, session: PaymentSession, db_session
    ) -> list:
        """Schedule all reminders for a payment session."""
        ...


async def node(
    state: BookingState,
    scheduler: Optional[ReminderScheduler] = None,
    on_failure: str = "log",
) -> BookingState:
    """Schedule payment reminders - NON-BLOCKING.

    Failure to schedule reminders does NOT stop the workflow.
    Logs error and continues.

    Args:
        state: Current workflow state
        scheduler: ReminderScheduler implementation (default: reminder_service)
        on_failure: "log" (continue) or "raise" (stop workflow)

    Returns:
        Updated state with payment_reminders_scheduled count
    """
    if scheduler is None:
        scheduler = reminder_service

    session_id = state.get("payment_session_id")
    if not session_id:
        logger.warning("⚠️ No payment_session_id - skipping reminders")
        return state

    try:
        async with await db_connection.get_session() as db_session:
            from sqlmodel import select

            # Fetch PaymentSession
            result = await db_session.execute(
                select(PaymentSession).where(
                    PaymentSession.session_id == session_id
                )
            )
            session = result.scalar_one_or_none()

            if not session:
                raise ValueError(f"Session not found: {session_id}")

            # Schedule reminders
            reminders = await scheduler.schedule_reminders(session, db_session)
            state["payment_reminders_scheduled"] = len(reminders)

            logger.info(f"✅ Scheduled {len(reminders)} reminders")

    except Exception as e:
        logger.error(f"❌ Failed to schedule reminders: {e}")

        if on_failure == "raise":
            raise

        # Non-blocking: add error but continue
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append("reminder_scheduling_failed")

    return state
