from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from models.audit import AuditAction, AuditLevel


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: AuditAction
    resource: str
    resource_id: Optional[str] = None
    details: Dict[str, Any]
    ip_address: str
    user_agent: Optional[str] = None
    timestamp: datetime
    level: AuditLevel
    success: bool
    error_message: Optional[str] = None


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    size: int


class SessionLogResponse(BaseModel):
    id: str
    user_id: str
    username: str
    session_id: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    ip_address: str
    user_agent: Optional[str] = None
    is_active: bool
    last_activity: datetime


class AuditSearchFilters(BaseModel):
    user_id: Optional[str] = None
    action: Optional[AuditAction] = None
    resource: Optional[str] = None
    level: Optional[AuditLevel] = None
    success: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    ip_address: Optional[str] = None