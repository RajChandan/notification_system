from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications import Notification, NotificationStatus
from app.models.outbox import NotificationOutbox
from app.models.notifications_dlq import NotificationDLQ, DLQStatus


class RetryService:
    def __init__(self, max_retry_count: int, retry_delays: dict[int, int], dlq_service):
        self.max_retry_count = max_retry_count
        self.retry_delays = retry_delays
        self.dlq_service = dlq_service

    async def move_to_dlq(
        self,
        db,
        notification,
        event: dict,
        failure_reason: str,
        error_type: str | None = None,
        original_outbox_id: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        notification.status = NotificationStatus.FAILED
        notification.last_error = failure_reason
        notification.failed_at = now

        dlq_record = NotificationDLQ(
            notification_id=notification.notification_id,
            channel=notification.channel,
            payload=event,
            failure_reason=failure_reason,
            error_type=error_type,
            retry_count=notification.retry_count,
            original_outbox_id=original_outbox_id,
            status=DLQStatus.PENDING,
        )

        dlq_event = {
            "notification_id": notification.notification_id,
            "failure_reason": failure_reason,
            "error_type": error_type,
            "retry_count": notification.retry_count,
            "payload": event,
            "failed_at": now.isoformat(),
        }

        dlq_outbox = NotificationOutbox(
            notification_id=notification.notification_id,
            payload=dlq_event,
            topic="notifications.dlq",
            published=False,
            attempt=notification.retry_count,
            available_at=now,
        )

        db.add(dlq_record)
        db.add(dlq_outbox)

        await db.commit()

    async def handle_failure(
        self, db: AsyncSession, notification: Notification, event: dict, reason: str
    ) -> None:
        notification.retry_count += 1
        current_attempt = notification.retry_count

        if current_attempt >= self.max_retry_count:
            await self.move_to_dlq(
                db=db, notification=notification, event=event, failure_reson=reason
            )
            return

        delay_seconds = self.retry_delays.get(current_attempt, 60)

        retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)

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
            notification_id=notification.notification_id,
            payload=retry_event,
            published=False,
            attempt=current_attempt,
            available_at=retry_at,
        )

        db.add(retry_outbox)
        await db.commit()

        print(
            f"Retry Scheduled : {notification.notification_id} , attempt : {current_attempt}, retry_at : {retry_at.isoformat()}"
        )
