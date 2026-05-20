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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TemplateType(str, Enum):
    TRANSACTIONAL = "transactional"
    PROMOTIONAL = "promotional"


class Template(Base):
    __tablename__ = "templates"

    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(255), nullable=False)
    channel = Column(Sqlenum(Channel), nullable=False)
    template_type = Column(Sqlenum(TemplateType), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=False)
