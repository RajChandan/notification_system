from enum import Enum
from sqlalchemy import (
    UUID,
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

from .notifications import Notification


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"

    outbox_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    notification_id = Column(
        UUID(as_uuid=True), ForeignKey("notifications.notification_id"), nullable=False
    )
    payload = Column(JSON, nullable=False)
    published = Column(Boolean, nullable=False, default=False)
    attempt = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    notification = relationship("Notification")

    # outbox_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # notification_id = Column(
    #     String(36), ForeignKey("notifications.notification_id"), nullable=False
    # )
    # payload = Column(JSON, nullable=False)
    # published = Column(Boolean, default=False)

    # created_at = Column(DateTime, default=datetime.utcnow)
    # published_at = Column(DateTime, nullable=True)

    # notification = relationship(Notification, back_populates="outbox")
