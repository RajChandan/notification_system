from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications import Notification, NotificationStatus
from app.models.outbox import NotificationOutbox


class RetryService:
    def __init__(self, max_retry_count: int, retry_delays: dict[int, int], dlq_service):
        self.max_retry_count = max_retry_count
        self.retry_delays = retry_delays
        self.dlq_service = dlq_service

    async def handle_failure(
        self, db: AsyncSession, notification: Notification, event: dict, reason: str
    ) -> None:
        notification.retry_count += 1
        current_attempt = notification.retry_attempt

        if current_attempt >= self.max_retry_count:
            notification.status = NotificationStatus.FAILED

            await self.dlq_service.publish(
                event=event, reason=reason, retry_count=current_attempt
            )

            await db.commit()

            print(
                f"moved to dlq {notification.notification_id},attempt:{current_attempt},reason={reason}"
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
