from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.utils import Channel
from ..models.notifications import Notification
from ..models.outbox import NotificationOutbox
from ..models.templates import Template
from .template_engine import TemplateEngine
from ..models.utils import NotificationStatus
from ..schemas.notifications import NotificationCreateRequest


class NotificationService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self, request: NotificationCreateRequest
    ) -> Notification:

        async with self.db.begin():
            print(
                f"Creating notification for user: {request.user_id}, template: {request.template_type}, channel: {request.channel}, recipient: {request.recipient}"
            )
            template = await self._get_template(request.template_type, request.channel)
            print(
                f"Fetched template: {template.template_id} for type: {request.template_type} and channel: {request.channel}"
            )
            payload = {
                "recipient": request.recipient,
                "variables": request.variables,
                "metadata": request.metadata,
            }
            rendered_content = TemplateEngine.render(template.content, payload)
            print(f"Rendered content: {rendered_content}")

            notification = Notification(
                user_id=request.user_id,
                channel=request.channel,
                payload={**payload, "rendered_content": rendered_content},
                status=NotificationStatus.PENDING,
                template_id=template.template_id,
            )
            self.db.add(notification)
            await self.db.flush()
            print(f"Created notification with ID: {notification.notification_id}")

            outbox_payload = {
                "notification_id": str(notification.notification_id),
                "user_id": request.user_id,
                "channel": request.channel,
                "recipient": request.recipient,
                "content": rendered_content,
                "metadata": request.metadata,
            }

            outbox = NotificationOutbox(
                notification_id=notification.notification_id,
                payload=outbox_payload,
                published=False,
            )

            self.db.add(outbox)

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
