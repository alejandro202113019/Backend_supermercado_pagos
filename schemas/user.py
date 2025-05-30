from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from models.user import UserRole, UserStatus


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: UserRole = UserRole.CLIENT


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    page: int
    size: int