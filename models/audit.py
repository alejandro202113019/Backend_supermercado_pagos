from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AuditAction(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    PAYMENT = "payment"
    PASSWORD_CHANGE = "password_change"
    # Agregar nuevas acciones válidas para evitar errores
    ACCESS = "access"
    USER_ACCESS = "user_access"
    PRODUCT_ACCESS = "product_access"
    ACCOUNT_ACCESS = "account_access"


class AuditLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: AuditAction
    resource: str  # e.g., "user", "product", "account"
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: str
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: AuditLevel = AuditLevel.INFO
    success: bool = True
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        exclude_none = True  # Excluir campos None al serializar


class SessionLog(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    username: str
    session_id: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    ip_address: str
    user_agent: Optional[str] = None
    is_active: bool = True
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        exclude_none = True  # Excluir campos None al serializar