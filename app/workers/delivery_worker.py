import asyncio
import json

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
from app.providers.factory import DeliveryProviderFactory

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

    async def start(self):
        await self.consumer.start()
        await self.producer.start()
        try:
            async for message in self.consumer:
                event = json.loads(message.value.decode("utf-8"))

                await self.process_event(event)

                await self.consumer.commit()

        finally:
            await self.consumer.stop()
            await self.producer.stop()
            await self.redis.close()

    async def process_event(self, event: dict):
        notification_id = event["notification_id"]
        # channel = event["channel"]
        # recipient = event["recipient"]
        # content = event["content"]
        # metadata = event.get("metadata", {})
        idempotency_key = f"notification:sent:{notification_id}"

        async with AsyncSessionLocal() as db:
            notification = await db.get(Notification, notification_id)

            if not notification:
                await self.publish_to_dlq(event=event, reason="notification_not_found")
                return

            if notification.status == NotificationStatus.SENT:
                print(f"Already sent : {notification_id}")
                return

            locked = await self.redis.set(idempotency_key, "processing", nx=True, ex=60)

            if not locked:
                print(f"duplicate skipped : {notification_id}")
                return

            try:
                channel = Channel(event["channel"])
                provider = DeliveryProviderFactory.get_provider(channel)

                success = await provider.send(
                    recipient=event["recipient"],
                    content=event["content"],
                    metadata=event.get("metadata", {}),
                )

                if success:
                    notification.status = NotificationStatus.SENT
                    await self.redis.set(idempotency_key, "sent", ex=3600)
                    await db.commit()
                    print(f"Notification sent : {notification_id}")
                    return

                await self.handle_failure(
                    db=db,
                    notification=notification,
                    event=event,
                    reason="provider_return_false",
                    idempotency_key=idempotency_key,
                )

            except Exception as e:
                await self.handle_failure(
                    db=db,
                    notification=notification,
                    event=event,
                    reason=str(e),
                    idempotency_key=idempotency_key,
                )

    async def handle_failure(
        self,
        db,
        notification: Notification,
        event: dict,
        reason: str,
        idempotency_key: str,
    ):
        notification.retry_count += 1
        current_attempt = notification.retry_count
        if current_attempt >= MAX_RETRY_COUNT:
            notification.status = NotificationStatus.FAILED

            await self.publish_to_dlq(
                event=event, reason=reason, retry_count=current_attempt
            )
            print(f"moved to dlq : {notification.notification_id} reason : {reason}")

        else:
            notification.status = NotificationStatus.RETRYING
            print(
                f"marked for retry : {notification.notification_id} retry_count : {notification.retry_count}"
            )

        await self.redis.delete(idempotency_key)
        await db.commit()

    async def publish_to_dlq(self, event: dict, reason: str):
        dlq_payload = {**event, "dlq_reason": reason}
        await self.producer.send_and_wait(
            NOTIFICATION_DLQ_TOPIC,
            key=event.get("notification_id", "unknown").encode("utf-8"),
            value=json.dumps(dlq_payload).encode("utf-8"),
        )


async def main():
    worker = DeliveryWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
