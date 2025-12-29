"""Payment Celery tasks.

Background tasks for payment processing and management.
"""

import asyncio
import logging

from celery import shared_task
from sqlmodel import select

from db.connection import db_connection
from models import PaymentReminder, ReminderStatus
from tasks import celery_app

logger = logging.getLogger(__name__)


@shared_task(
    name="tasks.payment_tasks.cancel_pending_reminders",
    bind=True,
)
def cancel_pending_reminders(self, session_id: str) -> dict:
    """Cancel all pending reminder tasks for a payment session.

    Called when admin confirms payment. Revokes pending Celery tasks
    and marks reminder records as CANCELLED.

    Args:
        session_id: UUID of PaymentSession

    Returns:
        Dict with cancellation summary
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_cancel_reminders_async(session_id))


async def _cancel_reminders_async(session_id: str) -> dict:
    """Async implementation of reminder cancellation."""
    async with await db_connection.get_session() as db_session:
        # Fetch all SCHEDULED reminders for this session
        result = await db_session.execute(
            select(PaymentReminder).where(
                PaymentReminder.session_id == session_id,
                PaymentReminder.status == ReminderStatus.SCHEDULED,
            )
        )
        reminders = result.scalars().all()

        cancelled_count = 0
        failed_count = 0

        # Revoke each Celery task
        for reminder in reminders:
            if reminder.celery_task_id:
                try:
                    celery_app.control.revoke(
                        reminder.celery_task_id,
                        terminate=True,
                        signal="SIGKILL",
                    )
                    cancelled_count += 1
                    logger.info(f"⏹️ Revoked task: {reminder.celery_task_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to revoke task: {e}")
                    failed_count += 1

            # Mark reminder as CANCELLED
            reminder.status = ReminderStatus.CANCELLED
            db_session.add(reminder)

        await db_session.commit()

        logger.info(
            f"✅ Cancelled {cancelled_count} reminders "
            f"({failed_count} failures)"
        )

        return {
            "status": "cancelled",
            "session_id": session_id,
            "cancelled": cancelled_count,
            "failed": failed_count,
        }
