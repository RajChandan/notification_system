# create_tables.py

import asyncio

from app.db.session import engine
from app.db.base import Base
from app.models.notifications import Notification
from app.models.outbox import NotificationOutbox
from app.models.templates import Template
from app.models.notifications_dlq import NotificationDLQ


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Tables created successfully")


asyncio.run(main())
