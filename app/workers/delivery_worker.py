import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.factory import DeliveryProviderFactory

from ..models.utils import Channel, NotificationStatus
from ..models.notifications import Notification


class DeliveryWorker:
    def __init__(self, db: AsyncSession, kafka_consumer, redis_client):
        self.db = db
        self.kafka_consumer = kafka_consumer
        self.redis = redis_client

    async def start(self):
        async for message in self.kafka_consumer:
            event = json.loads(message.value.decode())

            await self.process_event(event)

    async def process_event(self, event: dict):
        notification_id = event.get("notification_id")
        idempotency_key = f"notification:sent:{notification_id}"

        already_processed = await self.redis.get(idempotency_key)

        if already_processed:
            return

        channel = Channel(event.get("channel"))

        provider = DeliveryProviderFactory.get_provider(channel)

        success = await provider.send()

        if success:
            await self.redis.set(idempotency_key, "1", ex=86400)
            await self._mark_sent(notification_id)

        else:
            self._mark_failed(notification_id)

    async def _mark_sent(self, notification_id: str):
        notification = await self.db.get(Notification, notification_id)
        notification.status = NotificationStatus.SENT
        await self.db.commit()

    async def _mark_failed(self, notification_id: str):
        notification = await self.db.get(Notification, notification_id)
        notification.status = NotificationStatus.FAILED
        notification.retry_count += 1
        await self.db.commit()
