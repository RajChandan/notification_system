import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications import Notification, NotificationStatus
from app.models.outbox import NotificationOutbox
from app.models.notifications_dlq import NotificationDLQ, DLQStatus
from app.services.dlq_service import DLQService

logger = logging.getLogger(__name__)


class RetryService:
    DELIVERY_TOPIC = "notifications.delivery"

    def __init__(
        self,
        max_retry_count: int,
        retry_delays: dict[int, int],
        dlq_service: DLQService,
    ) -> None:
        if max_retry_count < 1:
            raise ValueError("max_retry_count must be atleast 1")
        self.max_retry_count = max_retry_count
        self.retry_delays = retry_delays
        self.dlq_service = dlq_service

    async def move_to_dlq(
        self,
        db,
        notification: Notification,
        event: dict[str, Any],
        failure_reason: str,
        error_type: str | None = None,
        original_outbox_id: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        notification.status = NotificationStatus.FAILED
        notification.last_error = failure_reason
        notification.failed_at = now

        try:

            dlq_record = await self.dlq_service.create_dlq_record(
                db=db,
                notification=notification,
                event=event,
                failure_reason=failure_reason,
                error_type=error_type,
                original_outbox_id=original_outbox_id,
            )
            await db.commit()

        except Exception:
            await db.rollback()
            logger.exception(
                "failed to move notification to dlq",
                extra={
                    "notification_id": str(notification.notification_id),
                    "retry_count": notification.retry_count,
                },
            )

            raise

        logger.error(
            "Notification moved to dlq",
            extra={
                "event": "notification_moved_to_dlq",
                "notfication_id": str(notification.notification_id),
                "dlq_id": str(dlq_record.dlq_id),
                "retry_count": notification.retry_count,
                "failure_reason": failure_reason,
                "channel": notification.channel.value,
                "error_type": error_type,
            },
        )

    async def handle_failure(
        self,
        db: AsyncSession,
        notification: Notification,
        event: dict[str, Any],
        reason: str,
        error_type: str | None = None,
        original_outbox_id: str | None = None,
    ) -> None:
        notification.retry_count = (notification.retry_count or 0) + 1

        current_attempt = notification.retry_count

        notification.last_error = reason

        if current_attempt >= self.max_retry_count:
            await self.move_to_dlq(
                db=db,
                notification=notification,
                event=event,
                failure_reason=reason,
                error_type=error_type,
                original_outbox_id=original_outbox_id,
            )
            return

        await self.schedule_retry(
            db=db,
            notification=notification,
            event=event,
            current_attempt=current_attempt,
            failure_reason=reason,
        )

    async def schedule_retry(
        self,
        db: AsyncSession,
        notification: Notification,
        event: dict[str, Any],
        current_attempt: int,
        failure_reason: str,
    ) -> None:
        delay_seconds = self.retry_delays.get(current_attempt, 60)

        retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        notification.status = NotificationStatus.RETRYING

        retry_event = {
            "notification_id": str(notification.notification_id),
            "user_id": event.get("user_id"),
            "channel": event["channel"],
            "recipient": event["recipient"],
            "content": event["content"],
            "metadata": event.get("metadata", {}),
        }

        retry_outbox = NotificationOutbox(
            notification_id=str(notification.notification_id),
            payload=retry_event,
            topic=self.DELIVERY_TOPIC,
            published=False,
            attempt=current_attempt,
            available_at=retry_at,
        )

        db.add(retry_outbox)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception(
                "failed to schedule notification retry",
                extra={
                    "event": "retry_schedule_failed",
                    "notification_id": str(notification.notification_id),
                    "attempt": current_attempt,
                },
            )

            raise
        logger.warning(
            "Notification retry scheduled",
            extra={
                "event": "retry_scheduled",
                "notification_id": str(notification.notification_id),
                "attempt": current_attempt,
                "retry_at": retry_at.isoformat(),
                "channel": notification.channel.value,
                "failure_reason": failure_reason,
            },
        )
