from enum import Enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    JSON,
    Text,
    Enum as Sqlenum,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

from .utils import Channel, NotificationStatus, PriorityLevel
from app.db.base import Base


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    channel = Column(Sqlenum(Channel), nullable=False)
    template_id = Column(
        String(36), ForeignKey("templates.template_id"), nullable=False
    )
    payload = Column(JSON, nullable=False)
    status = Column(Sqlenum(NotificationStatus), default=NotificationStatus.PENDING)
    priority = Column(Sqlenum(PriorityLevel), default=PriorityLevel.MEDIUM)
    retry_count = Column(Integer, default=0)
    scheduled_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("Template")
