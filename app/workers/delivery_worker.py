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
        processing_key = f"notification:processing:{notification_id}"
        sent_key = f"notification:sent:{notification_id}"
        idempotency_key = f"notification:sent:{notification_id}"

        already_sent = await self.redis.exists(sent_key)
        if already_sent:
            print(f"Already sent : {notification_id}")
            return

        lock_acquired = await self.redis.set(processing_key, "1", nx=True, ex=300)
        if not lock_acquired:
            print(f"Already being processed : {notification_id}")
            return

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
                event=event,
                reason=reason,
                retry_count=current_attempt,
                retry_count=current_attempt,
            )
            await self.redis.delete(idempotency_key)
            await db.commit()
            print(
                f"notification moved to dlq : {notification.notification_id} reason : {reason} attempt : {current_attempt}"
            )
            return

        delay_seconds = RETRY_DELAY_SECONDS.get(current_attempt, 60)
        retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        notification.status = NotificationStatus.RETRYING

        retry_payload = {
            "notification_id": str(notification.notification_id),
            "user_id": event.get("user_id"),
            "channel": event["channel"],
            "recipient": event["recipient"],
            "content": event["content"],
            "metadata": event.get("metadata", {}),
        }

        retry_outbox = NotificationOutbox(
            notification_id=notification.notification_id,
            payload=retry_payload,
            published=False,
            attempt=current_attempt,
            available_at=retry_at,
        )

        db.add(retry_outbox)

        await self.redis.delete(idempotency_key)
        await db.commit()

        print(
            f"Retry scheduled : id : {notification.notification_id}, attempt : {current_attempt} retry_at : {retry_at.isoformat()} reason : {reason}"
        )

    async def publish_to_dlq(self, event: dict, reason: str, retry_count: int) -> None:
        dlq_payload = {
            **event,
            "retry_count": retry_count,
            "dlq_reason": reason,
            "failed_at": datetime.utcnow().isoformat(),
        }
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
