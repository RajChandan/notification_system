from pydantic import BaseModel
from typing import Any
from datetime import datetime

from app.models.notifications import Channel, PriorityLevel


class NotificationCreateRequest(BaseModel):
    user_id: str
    template_type: str
    channel: Channel
    recipient: str
    variables: dict[str, Any]
    metadata: dict[str, Any] = {}
    priority: PriorityLevel = PriorityLevel.MEDIUM
    scheduled_at: datetime | None = None
