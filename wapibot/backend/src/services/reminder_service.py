"""Payment reminder scheduling service.

Calculates reminder schedule from configuration and coordinates
Celery task scheduling for background reminders.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from core.config import settings
from models.payment_session import PaymentSession
from models.payment_reminder import PaymentReminder, ReminderStatus

logger = logging.getLogger(__name__)


class ReminderSchedulingService:
    """Service for scheduling payment reminders via Celery."""

    def __init__(self):
        """Initialize with configuration from settings."""
        self.reminder_intervals = settings.payment_reminder_intervals
        self.cutoff_hours = settings.payment_cutoff_hours
        self.send_instant_reminder = settings.payment_instant_reminder
        logger.info(
            f"Reminder config: instant={self.send_instant_reminder}, "
            f"intervals={self.reminder_intervals}h, "
            f"cutoff={self.cutoff_hours}h"
        )

    def calculate_reminder_schedule(
        self, session_created_at: datetime
    ) -> List[datetime]:
        """Calculate all reminder send times from creation time.

        Schedule includes:
        - Instant reminder (0 sec) if send_instant_reminder=True
        - Subsequent reminders at intervals from config

        Args:
            session_created_at: When the payment session was created

        Returns:
            List of datetime when reminders should be sent
        """
        schedule = []

        # Add instant reminder if configured
        if self.send_instant_reminder:
            schedule.append(session_created_at)

        # Add interval-based reminders
        for interval_hours in self.reminder_intervals:
            send_at = session_created_at + timedelta(hours=interval_hours)
            schedule.append(send_at)

        logger.debug(f"Reminder schedule: {[s.isoformat() for s in schedule]}")
        return schedule

    def calculate_expiry_time(self, session_created_at: datetime) -> datetime:
        """Calculate when payment request expires.

        Args:
            session_created_at: When the payment session was created

        Returns:
            Expiry datetime (cutoff_hours from creation)
        """
        expiry = session_created_at + timedelta(hours=self.cutoff_hours)
        logger.debug(f"Payment expiry: {expiry.isoformat()}")
        return expiry

    async def schedule_reminders(
        self, session: PaymentSession, db_session
    ) -> List[PaymentReminder]:
        """Schedule all reminders for a payment session via Celery.

        Creates PaymentReminder records and queues Celery tasks
        with proper delays to send at scheduled times.

        Args:
            session: PaymentSession to schedule reminders for
            db_session: SQLModel async session for persistence

        Returns:
            List of created PaymentReminder records

        Raises:
            ValueError: If session not found in database
        """
        from tasks.reminder_tasks import send_payment_reminder

        schedule = self.calculate_reminder_schedule(session.created_at)
        reminders = []
        now = datetime.now()

        for idx, send_at in enumerate(schedule):
            # Create reminder record
            reminder = PaymentReminder(
                session_id=session.session_id,
                reminder_number=idx,
                scheduled_at=send_at,
                status=ReminderStatus.SCHEDULED,
            )

            # Calculate delay in seconds
            delay_seconds = (send_at - now).total_seconds()

            # Queue Celery task
            if delay_seconds <= 0:
                # Send immediately
                task = send_payment_reminder.apply_async(
                    args=[session.session_id], countdown=0
                )
            else:
                # Schedule for future
                task = send_payment_reminder.apply_async(
                    args=[session.session_id], countdown=int(delay_seconds)
                )

            # Store Celery task ID for later cancellation
            reminder.celery_task_id = task.id
            db_session.add(reminder)
            reminders.append(reminder)

            logger.info(
                f"Scheduled reminder {idx} for {send_at.isoformat()} "
                f"(task_id={task.id})"
            )

        await db_session.commit()
        return reminders


# Singleton instance
reminder_service = ReminderSchedulingService()
