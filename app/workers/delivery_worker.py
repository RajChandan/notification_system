import asyncio
import json
from datetime import datetime, timedelta
from redis.asyncio import Redis
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.core.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    NOTIFICATION_TOPIC,
    NOTIFICATION_DLQ_TOPIC,
    MAX_RETRY_COUNT,
    RETRY_DELAY_SECONDS,
)
from app.db.session import AsyncSessionLocal
from app.models.notifications import Notification, NotificationStatus
from app.models.utils import Channel
from app.models.outbox import NotificationOutbox
from app.providers.factory import DeliveryProviderFactory

from app.services.delivery_service import DeliveryService
from app.services.dlq_service import DLQService
from app.services.idempotency_service import IdempotencyService
from app.services.retry_service import RetryService

# redis = Redis(host="localhost", port=6380, decode_responses=True)


class DeliveryWorker:
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            NOTIFICATION_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="notification-delivery-workers",
            enable_auto_commit=False,
        )
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        self.redis = Redis(host="localhost", port=6380, decode_responses=True)
        self.delivery_service = DeliveryService()
        self.idempotency_service = IdempotencyService(self.redis)

        self.dlq_service = DLQService()

        self.retry_service = RetryService(
            max_retry_count=MAX_RETRY_COUNT,
            retry_delays=RETRY_DELAY_SECONDS,
            dlq_service=self.dlq_service,
        )

    async def start(self):
        await self.consumer.start()
        await self.producer.start()
        try:
            async for message in self.consumer:
                event = json.loads(message.value.decode("utf-8"))

                try:

                    await self.process_event(event)
                except Exception as e:
                    print(f"unexpected worker error : {e}")
                    continue

                await self.consumer.commit()

        finally:
            await self.consumer.stop()
            await self.producer.stop()
            await self.redis.close()

    async def process_event(self, event: dict) -> None:
        notification_id = event["notification_id"]

        if await self.idempotency_service.is_sent(notification_id):
            print(f"Already sent : skipping : {notification_id}")
            return

        lock_acquired = await self.idempotency_service.acquire_processing_lock(
            notification_id
        )

        if not lock_acquired:
            print(f"Already being processed : {notification_id}")
            return

        try:
            async with AsyncSessionLocal() as db:
                notification = await db.get(Notification, notification_id)
                if not notification:
                    await self.dlq_service.publish(
                        event=event, reason="notification_not_found", retry_count=0
                    )

                    return

                if notification.status == NotificationStatus.SENT:
                    await self.idempotency_service.mark_sent(notification_id)
                    return

                try:
                    success = await self.delivery_service.deliver(event)

                except Exception as e:
                    await self.retry_service.handle_failure(
                        db=db,
                        notification=notification,
                        event=event,
                        reason=str(e),
                        error_type=type(e).__name__,
                        original_outbox_id=event.get("outbox_id"),
                    )
                    return

                if not success:
                    await self.retry_service.handle_failure(
                        db=db,
                        notification=notification,
                        event=event,
                        reason="provider_return_false",
                        error_type="DeliveryFailed",
                        original_outbox_id=event.get("outbox_id"),
                    )
                    return

                notification.status = NotificationStatus.SENT

                await db.commit()

                await self.idempotency_service.mark_sent(notification_id)
                print(f"Notification sent : {notification_id}")

        finally:
            await self.idempotency_service.release_processing_lock(notification_id)


async def main():
    worker = DeliveryWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
