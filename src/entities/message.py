from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from src.database.core import Base
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    SYSTEM = "system"



class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)
    file_url = Column(String, nullable=True)  # For images, videos, files
    file_name = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    conversation = relationship("Conversation", back_populates="messages")
    read_receipts = relationship("MessageReadReceipt", back_populates="message")
