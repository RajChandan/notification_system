from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.utils import Channel
from ..models.notifications import Notification
from ..models.outbox import NotificationOutbox
from ..models.templates import Template
from .template_engine import TemplateEngine
from ..models.utils import NotificationStatus


class NotificationService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: int,
        template_type: str,
        channel: Channel,
        payload: dict,
        scheduled_at=None,
    ) -> Notification:
        print(
            f"Creating notification for user_id: {user_id}, template_type: {template_type}, channel: {channel}, payload: {payload}"
        )
        async with self.db.begin():
            template = await self._get_template(template_type, channel)
            print(
                f"Fetched template: {template.template_id} for type: {template_type} and channel: {channel}"
            )
            rendered_content = TemplateEngine.render(template.content, payload)
            print(f"Rendered content: {rendered_content}")

            notification = Notification(
                user_id=user_id,
                channel=channel,
                payload={**payload, "rendered_content": rendered_content},
                status=NotificationStatus.PENDING,
                template_id=template.template_id,
            )
            self.db.add(notification)
            await self.db.flush()
            print(f"Created notification with ID: {notification.notification_id}")

            # outbox_payload = {
            #     "notification_id": str(notification.notification_id),
            #     "user_id": user_id,
            #     "channel": channel,
            #     "recipient": payload.get("recipient"),
            #     "content": rendered_content,
            #     "metadata": payload.get("metadata", {}),
            # }

            # outbox = NotificationOutbox(
            #     notification_id=notification.id,
            #     payload=outbox_payload,
            #     published_flag=False,
            # )

            # self.db.add(outbox)

            return notification

    async def _get_template(self, template_type: str, channel: Channel) -> Template:
        result = await self.db.execute(
            select(Template).where(
                Template.template_type == template_type, Template.channel == channel
            )
        )

        template = result.scalar_one_or_none()

        if not template:
            raise ValueError(
                f"Template not found for type {template_type} and channel {channel}"
            )

        return template
