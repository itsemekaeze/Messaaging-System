from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_online: bool
    last_seen: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None