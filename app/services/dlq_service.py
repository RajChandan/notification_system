import logging

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notifications import Notification
from app.models.notifications_dlq import NotificationDLQ, DLQStatus
from app.models.outbox import NotificationOutbox

logger = logging.getLogger(__name__)


class DLQService:
    DLQ_TOPIC = "notifications.dlq"

    async def create_dlq_record(
        self,
        db: AsyncSession,
        notification: Notification,
        event: dict[str, Any],
        failure_reason: str,
        error_type: str | None = None,
        original_outbox_id: str | None = None,
    ) -> NotificationDLQ:
        now = datetime.now(timezone.utc)

        dlq_record = NotificationDLQ(
            notification_id=str(notification.notification_id),
            channel=notification.channel,
            payload=event,
            failure_reason=failure_reason,
            error_type=error_type,
            retry_count=notification.retry_count,
            original_outbox_id=original_outbox_id,
            status=DLQStatus.PENDING,
        )

        logger.info(
            "DLQ database record prepared",
            extra={
                "event": "dlq_record_created",
                "dlq_id": str(dlq_record.dlq_id),
                "notification_id": str(notification.notification_id),
                "retry_count": notification.retry_count,
            },
        )

        db.add(dlq_record)

        await db.flush()

        dlq_event = {
            "dlq_id": str(dlq_record.dlq_id),
            "notification_id": str(notification.notification_id),
            "failure_reason": failure_reason,
            "error_type": error_type,
            "retry_count": notification.retry_count,
            "payload": event,
            "failed_at": now.isoformat(),
        }

        dlq_outbox = NotificationOutbox(
            notification_id=str(notification.notification_id),
            payload=dlq_event,
            topic=self.DLQ_TOPIC,
            published=False,
            attempt=notification.retry_count,
            available_at=now,
        )

        db.add(dlq_outbox)
        return dlq_record
