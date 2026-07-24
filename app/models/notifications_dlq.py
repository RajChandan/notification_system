import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from enum import Enum

from app.db.base import Base

from app.models.utils import Channel


class DLQStatus(str, Enum):
    PENDING = "pending"
    REPLAYING = "replaying"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    REPLAY_FAILED = "relpay_failed"


class NotificationDLQ(Base):
    __tablename__ = "notification_dlq"

    dlq_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = Column(String(36), ForeignKey("notifications.notification_id"))
    channel = Column(Enum(Channel), nullable=False)
    payload = Column(JSON, nullable=False)
    failure_reason = Column(Text, nullable=False)
    error_type = Column(String(255), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    original_outbox_id = Column(String(36), nullable=True)
    status = Column(
        Enum(DLQStatus), nullable=False, default=DLQStatus.PENDING, index=True
    )
    replay_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_replayed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(Text, nullable=True)
