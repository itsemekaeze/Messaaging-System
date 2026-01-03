from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.users.models import UserResponse

class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    message_type: str = "text"

class MessageEdit(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    message_type: str
    file_url: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    is_edited: bool
    is_deleted: bool
    edited_at: Optional[datetime]
    created_at: datetime
    sender: UserResponse
    read_by: List[str] = []
    
    class Config:
        from_attributes = True


