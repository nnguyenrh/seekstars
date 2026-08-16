from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from .enums import UserRole


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=8, description="Plaintext password (hashed before storage)")
    display_name: Optional[str] = Field(None, description="Friendly display name")


class User(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    role: UserRole = UserRole.USER
    created_at: datetime


class UserLogin(BaseModel):
    username: str
    password: str
