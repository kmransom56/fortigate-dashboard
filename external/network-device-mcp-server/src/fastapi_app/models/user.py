""
User model and related schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"

class UserBase(BaseModel):
    """Base user model with common attributes"""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8)

class UserInDB(UserBase):
    """User model stored in DB"""
    id: str
    hashed_password: str
    
    class Config:
        orm_mode = True

class User(UserBase):
    """User model for API responses"""
    id: str
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None
    scopes: List[str] = []
