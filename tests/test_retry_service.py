from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.notifications import NotificationStatus
from app.services.retry_service import RetryService


def make_notification(retry_count=0):
    notification = MagicMock()
    notification.notification_id = "notification-123"
    notification.retry_count = retry_count
    notification.status = NotificationStatus.PENDING
    notification.channel.value = "email"

    return notification


def make_event():
    return {
        "notification_id": "notification-123",
        "user_id": "user-123",
        "channel": "email",
        "recipient": "test@example.com",
        "content": "Hello, Chandan",
        "metadata": {"subject": "welcome"},
    }


@pytest.mark.asyncio
async def test_first_failure_schedules_retry():
    db = AsyncMock()
    dlq_service = AsyncMock()

    service = RetryService(
        max_retry_count=3, retry_delays={1: 5, 2: 10}, dlq_service=dlq_service
    )

    notification = make_notification(retry_count=0)

    await service.handle_failure(
        db=db,
        notification=notification,
        event=make_event(),
        reason="provider_unavailable",
    )

    assert notification.retry_count == 1
    assert notification.status == NotificationStatus.RETRYING

    db.add.assert_called_once()
    db.commit.assert_awaited_once()

    dlq_service.create_dlq_record.assert_not_awaited()
