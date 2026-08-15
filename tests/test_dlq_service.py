from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.dlq_service import DLQService


@pytest.mark.asyncio
async def test_create_dlq_record():
    db = AsyncMock()
    notification = MagicMock()

    notification.notification_id = "notification-123"

    notification.channel = "email"
    notification.retry_count = 3

    service = DLQService()

    event = {
        "notification_id": "notification-123",
        "channel": "email",
        "recipient": "test@example.com",
        "content": "Hello",
    }

    record = await service.create_dlq_record(
        db=db,
        notification=notification,
        event=event,
        failure_reason="provider timeout",
        error_type="TimeoutError",
    )

    assert record.notification_id == ("notification-123")

    assert record.failure_reason == ("provider timeout")

    assert record.retry_count == 3

    assert db.add.call_count == 2

    db.flush.assert_awaited_once()

    db.commit.assert_not_awaited()
