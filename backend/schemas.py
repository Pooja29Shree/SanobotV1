from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    message: str

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total_count: int

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class MessageResponse(BaseModel):
    msg: str