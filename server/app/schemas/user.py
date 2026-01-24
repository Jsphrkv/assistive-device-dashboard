from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """Schema for updating user"""
    full_name: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    """Complete user schema"""
    id: str
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(User):
    """User schema with hashed password (for DB)"""
    hashed_password: str