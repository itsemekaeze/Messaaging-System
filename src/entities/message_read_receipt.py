from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.core import Base


class MessageReadReceipt(Base):
    __tablename__ = "message_read_receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("Message", back_populates="read_receipts")
    
    __table_args__ = (
        Index('idx_message_user_receipt', 'message_id', 'user_id'),
    )