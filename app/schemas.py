from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class PaperResponse(BaseModel):
    id: int
    user_id: int
    title: str
    status: str
    chunk_count: int

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    paper_id: str
    message: str = ""
