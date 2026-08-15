from unittest.mock import AsyncMock

import pytest
from app.services.idempotency_service import IdempotencyService


@pytest.mark.asyncio
async def test_acquire_processing_lock():
    redis = AsyncMock()
    redis.set.return_value = True

    service = IdempotencyService(redis)

    result = await service.acquire_processing_lock("notification-123")
    assert result is True

    redis.set.assert_awaited_once_with(
        "notification:processing:notification-123",
        "1",
        nx=True,
        ex=300,
    )


@pytest.mark.asyncio
async def test_processing_lock_already_exists():
    redis = AsyncMock()

    redis.set.return_value = None

    service = IdempotencyService(redis)

    result = await service.acquire_processing_lock("notification-123")

    assert result is False


@pytest.mark.asyncio
async def test_notification_already_sent():
    redis = AsyncMock()
    redis.exists.return_value = 1
    service = IdempotencyService(redis)

    result = await service.is_sent("notification-123")

    assert result is True
