import asyncio

from app.services.outbox_publisher import OutboxPublisher


async def main():
    publisher = OutboxPublisher()

    while True:
        await publisher.publish_pending_events()
        await asyncio.sleep(5)


asyncio.run(main())
