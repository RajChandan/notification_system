import logging
import asyncio
import json
from datetime import datetime
from aiokafka import AIOKafkaProducer
from sqlalchemy import select

from app.core.config import KAFKA_BOOTSTRAP_SERVERS, NOTIFICATION_TOPIC
from app.db.session import AsyncSessionLocal

# from app.models.notifications import NotificationOutbox
from app.models.outbox import NotificationOutbox

logger = logging.getLogger(__name__)


class OutboxPublisher:
    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

    async def start(self) -> None:
        await self.producer.start()
        logger.info(
            "Outbox publisher started",
            extra={"event": "outbox_publisher_started", "topic": NOTIFICATION_TOPIC},
        )

        try:
            while True:
                published_count = await self.publish_pending_outbox()
                if published_count == 0:
                    await asyncio.sleep(5)

        finally:
            await self.producer.stop()

    async def publish_pending_outbox(self) -> int:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(NotificationOutbox)
                .where(
                    NotificationOutbox.published.is_(False),
                    NotificationOutbox.available_at <= datetime.utcnow(),
                )
                .order_by(NotificationOutbox.available_at)
                .limit(100)
            )

            rows = result.scalars().all()

            if not rows:
                print("No unpublished outbox rows")
                return

            for row in rows:
                event = {
                    **row.payload,
                    "attemp": row.attempt,
                    "outbox_id": str(row.outbox_id),
                }

                await self.producer.send_and_wait(
                    NOTIFICATION_TOPIC,
                    key=str(row.notification_id).encode("utf-8"),
                    value=json.dumps(event).encode("utf-8"),
                )

                row.published = True
                row.published_at = datetime.utcnow()

            await db.commit()

            if rows:
                print(f"Published {len(rows)} messages to kafka")
                logger.info(
                    "Outbox batch published",
                    extra={
                        "event": "outbox_batch_published",
                        "message_count": len(rows),
                    },
                )
            return len(rows)


async def main():
    publisher = OutboxPublisher()
    await publisher.start()


if __name__ == "__main__":
    asyncio.run(main())
