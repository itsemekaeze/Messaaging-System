from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.users.models import UserResponse
from src.message.models import MessageResponse


class ConversationCreate(BaseModel):
    participant_ids: List[str]
    name: Optional[str] = None
    is_group: bool = False

class ConversationUpdate(BaseModel):
    name: Optional[str] = None

class ParticipantResponse(BaseModel):
    user: UserResponse
    role: str
    joined_at: datetime
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    name: Optional[str]
    is_group: bool
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    participants: List[ParticipantResponse]
    last_message: Optional[MessageResponse] = None
    unread_count: int = 0
    my_role: Optional[str] = None
    
    class Config:
        from_attributes = True


class AddParticipantsRequest(BaseModel):
    user_ids: List[str]

class RemoveParticipantRequest(BaseModel):
    user_id: str

class TypingEvent(BaseModel):
    conversation_id: str
    is_typing: bool