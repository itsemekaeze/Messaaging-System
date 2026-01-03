from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.core import Base
from enum import Enum


class ParticipantRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(ParticipantRole), default=ParticipantRole.MEMBER)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_read_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # For removed participants
    left_at = Column(DateTime, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", back_populates="conversation_participants")
    
    __table_args__ = (
        Index('idx_conversation_user', 'conversation_id', 'user_id'),
    )