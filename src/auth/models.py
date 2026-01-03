from typing import Optional
from pydantic import BaseModel, validator


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    display_name: Optional[str] = None

    @validator('password')
    def validate_password_length(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot exceed 72 bytes')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str
    # user: UserResponse

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None