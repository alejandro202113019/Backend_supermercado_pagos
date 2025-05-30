from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: str
    username: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: UserRole = UserRole.CLIENT
    status: UserStatus = UserStatus.ACTIVE
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    last_failed_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    password_changed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True