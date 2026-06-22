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

from .utils import Channel, TemplateType
from app.db.base import Base


class Template(Base):
    __tablename__ = "templates"

    template_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_name = Column(String(255), nullable=False)
    channel = Column(Sqlenum(Channel), nullable=False)
    template_type = Column(Sqlenum(TemplateType), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=False)
