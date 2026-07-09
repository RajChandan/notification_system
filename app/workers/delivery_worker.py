import asyncio
import json

from redis.asyncio import Redis
from aiokafka import AIOKafkaConsumer
from app.core.config import KAFKA_BOOTSTRAP_SERVERS, NOTIFICATION_TOPIC
from app.db.session import AsyncSessionLocal
from app.models.notifications import Notification, NotificationStatus
from app.models.utils import Channel
from app.providers.factory import DeliveryProviderFactory

redis = Redis(host="localhost", port=6380, decode_responses=True)


class DeliveryWorker:
    def __init__(self):
        self.consumer = AIOKafkaConsumer(
            NOTIFICATION_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="notification-delivery-workers",
            enable_auto_commit=False,
        )

    async def start(self):
        await self.consumer.start()

        try:
            async for message in self.consumer:
                event = json.loads(message.value.decode("utf-8"))

                await self.process_event(event)

                await self.consumer.commit()

        finally:
            await self.consumer.stop()

    async def process_event(self, event: dict):
        notification_id = event["notification_id"]
        channel = event["channel"]
        recipient = event["recipient"]
        content = event["content"]
        metadata = event.get("metadata", {})

        provider = DeliveryProviderFactory.get_provider(channel)

        async with AsyncSessionLocal() as db:
            notification = await db.get(Notification, notification_id)

            if not notification:
                print(f"Notification not found : {notification_id}")

            if notification.status == NotificationStatus.SENT:
                print(f"Notification already sent : {notification_id}")
                return

            try:
                idempotency_key = f"notification:sent:{notification_id}"
                locked = await redis.set(
                    idempotency_key, "processing", nx=True, ex=86400
                )
                if not locked:
                    print(f"Duplicate Notification skipped : {notification_id}")
                success = await provider.send(recipient, content, metadata)
                if success:
                    notification.status = NotificationStatus.SENT
                    print(f"Notification sent successfully : {notification_id}")
                else:
                    notification.status = NotificationStatus.FAILED
                    notification.retry_count += 1
                    print(f"Notification failed to send : {notification_id}")

                await db.commit()

            except Exception as e:
                print(f"Delivery Failed : {str(e)}")
                notification.status = NotificationStatus.FAILED
                notification.retry_count += 1

                await db.commit()


async def main():
    worker = DeliveryWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
