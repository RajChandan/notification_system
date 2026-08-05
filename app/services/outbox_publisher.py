import logging
import json
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.outbox import NotificationOutbox

logging = logging.getLogger(__name__)


class OutboxPublisher:

    def __init__(self, db: AsyncSession, kafka_producer):
        self.db = db
        self.kafka_producer = kafka_producer

    async def publish_pending_events(self, batch_size=1000):
        result = await self.db.execute(
            select(NotificationOutbox)
            .where(NotificationOutbox.published_flag == False)
            .limit(batch_size)
        )

        rows = result.scalars().all()

        for row in rows:
            await self.kafka_producer.send_and_wait(
                topic="notifications.delivery",
                key=str(row.notification_id).encode(),
                value=json.dumps(row.payload).encode(),
            )

            row.published_flag = True

        await self.db.commit()
