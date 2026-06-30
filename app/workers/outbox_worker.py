import asyncio
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from ..models.notifications import Notification, NotificationStatus
from ..models.utils import Channel
from ..models.outbox import NotificationOutbox
from ..providers.factory import DeliveryProviderFactory


class OutboxWorker:
    async def process_pending_outbox(self):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(NotificationOutbox)
                .where(NotificationOutbox.published == False)
                .limit(10)
            )

            outbox_rows = result.scalars().all()
            if not outbox_rows:
                print("No pending outbox messages")
                return

            for outbox in outbox_rows:
                payload = outbox.payload

                notification_id = payload["notification_id"]
                channel = Channel(payload["channel"])
                recipient = payload["recipient"]
                content = payload["content"]
                metadata = payload.get("metadata", {})

                provider = DeliveryProviderFactory.get_provider(channel)

                try:
                    success = await provider.send(
                        recipient=recipient, content=content, metadata=metadata
                    )
                    notification = await db.get(Notification, notification_id)
                    if success:
                        notification.status = NotificationStatus.SENT
                        outbox.published = True
                        outbox.published_at = asyncio.get_event_loop().time()
                    else:
                        notification.status = NotificationStatus.FAILED
                        notification.retry_count += 1
                    await db.commit()

                except Exception as e:
                    print(f"Delivery failed : {str(e)}")
                    notification = await db.get(Notification, notification_id)
                    notification.status = NotificationStatus.FAILED
                    notification.retry_count += 1
                    await db.commit()


async def main():
    worker = OutboxWorker()

    while True:
        await worker.process_pending_outbox()
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
