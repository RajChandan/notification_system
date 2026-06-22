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
from app.db.base import Base
from datetime import datetime
import uuid


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"

    outbox_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = Column(
        String(36), ForeignKey("notifications.notification_id"), nullable=False
    )
    payload = Column(JSON, nullable=False)
    published = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    notification = relationship("Notification")
