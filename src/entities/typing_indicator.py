from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Integer
from datetime import datetime
from src.database.core import Base


class TypingIndicator(Base):
    __tablename__ = "typing_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_conversation_typing', 'conversation_id', 'user_id'),
    )