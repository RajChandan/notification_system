import asyncio
import json

from aiokafka import AIOKafkaProducer
from sqlalchemy import select

from app.core.config import KAFKA_BOOTSTRAP_SERVERS, NOTIFICATION_TOPIC
from app.db.session import AsyncSessionLocal

# from app.models.notifications import NotificationOutbox
from app.models.outbox import NotificationOutbox


class OutboxPublisher:
    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

    async def start(self):
        await self.producer.start()

        try:
            while True:
                await self.publish_pending_outbox()
                await asyncio.sleep(5)

        finally:
            await self.producer.stop()

    async def publish_pending_outbox(self):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(NotificationOutbox)
                .where(NotificationOutbox.published == False)
                .limit(100)
            )

            rows = result.scalars().all()

            if not rows:
                print("No unpublished outbox rows")
                return

            for row in rows:
                payload = row.payload
                await self.producer.send_and_wait(
                    NOTIFICATION_TOPIC,
                    key=str(row.notification_id).encode("utf-8"),
                    value=json.dumps(payload).encode("utf-8"),
                )

                row.published = True

            await db.commit()

            print(f"Published {len(rows)} messages to kafka")


async def main():
    publisher = OutboxPublisher()
    await publisher.start()


if __name__ == "__main__":
    asyncio.run(main())
