"""Payment reminder Celery tasks.

Background tasks for sending WhatsApp payment reminders.
"""

import asyncio
import logging
from datetime import datetime

from celery import shared_task
from sqlmodel import select

from db.connection import db_connection
from models import PaymentSession, PaymentStatus, PaymentTransaction, TransactionType, PaymentReminder, ReminderStatus
from clients.wapi.wapi_client import get_wapi_client

logger = logging.getLogger(__name__)


@shared_task(
    name="tasks.reminder_tasks.send_payment_reminder",
    bind=True,
    max_retries=2,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_payment_reminder(self, session_id: str) -> dict:
    """Send payment reminder WhatsApp message.

    Async Celery task that:
    1. Fetches PaymentSession from DB
    2. Checks if status is PENDING (skip if CONFIRMED/EXPIRED)
    3. Sends WhatsApp message with reminder
    4. Updates reminder_count and last_reminder_at
    5. Logs PaymentTransaction for audit trail

    Args:
        session_id: UUID of PaymentSession

    Returns:
        Dict with status ("sent", "skipped", or "failed")
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_send_reminder_async(session_id, self.request.id))


async def _send_reminder_async(session_id: str, task_id: str) -> dict:
    """Async implementation of reminder sending."""
    async with await db_connection.get_session() as db_session:
        # Fetch PaymentSession
        result = await db_session.execute(
            select(PaymentSession).where(
                PaymentSession.session_id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            logger.error(f"❌ Session not found: {session_id}")
            return {"status": "failed", "reason": "session_not_found"}

        # Skip if payment already confirmed or expired
        if session.status != PaymentStatus.PENDING:
            logger.info(
                f"⏭️ Skipping reminder - payment {session.status.value}"
            )
            return {"status": "skipped", "reason": f"payment_{session.status.value}"}

        # Build reminder message
        reminder_message = (
            "💳 *Payment Reminder*\n\n"
            f"Amount: ₹{session.amount:.2f}\n\n"
            "Please scan the QR code and complete your payment to confirm booking."
        )

        # Send via WhatsApp
        try:
            wapi_client = get_wapi_client()
            await wapi_client.send_message(
                phone_number=session.conversation_id,
                message_body=reminder_message,
            )
            logger.info(f"✅ Reminder sent to {session.conversation_id}")

        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {e}")
            return {"status": "failed", "reason": str(e)}

        # Update session
        session.reminder_count += 1
        session.last_reminder_at = datetime.now()
        db_session.add(session)

        # Log transaction
        transaction = PaymentTransaction(
            session_id=session_id,
            transaction_type=TransactionType.REMINDER_SENT,
            metadata={"reminder_number": session.reminder_count, "task_id": task_id},
        )
        db_session.add(transaction)

        # Update reminder record status
        result = await db_session.execute(
            select(PaymentReminder).where(
                PaymentReminder.celery_task_id == task_id
            )
        )
        reminder = result.scalar_one_or_none()
        if reminder:
            reminder.status = ReminderStatus.SENT
            reminder.sent_at = datetime.now()
            db_session.add(reminder)

        await db_session.commit()

        return {
            "status": "sent",
            "session_id": session_id,
            "reminder_number": session.reminder_count,
        }
