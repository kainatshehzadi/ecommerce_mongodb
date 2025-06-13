from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.constant import UserRole

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):  
    username: str
    password: str = Field(..., min_length=8)
    role:UserRole

class CreateUser(UserBase): 
    username: str
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=10, max_length=11)

class UserOut(UserBase):
    id: str
    username: str
    phone: Optional[str] 

class MessageResponse(BaseModel):
    message: str
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
class UserResponse(BaseModel):
    message: str
    