from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from models.account import AccountStatus, PaymentMethod, AccountItem, PaymentRecord


class AccountItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class AccountCreate(BaseModel):
    client_id: str
    items: List[AccountItemCreate]
    due_date: datetime
    discount: float = Field(default=0.0, ge=0)
    tax: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class AccountUpdate(BaseModel):
    items: Optional[List[AccountItemCreate]] = None
    due_date: Optional[datetime] = None
    discount: Optional[float] = Field(None, ge=0)
    tax: Optional[float] = Field(None, ge=0)
    status: Optional[AccountStatus] = None
    notes: Optional[str] = None


class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: PaymentMethod
    reference: Optional[str] = None


class AccountResponse(BaseModel):
    id: str
    account_number: str
    client_id: str
    client_name: str
    client_email: str
    items: List[AccountItem]
    subtotal: float
    tax: float
    discount: float
    total_amount: float
    status: AccountStatus
    due_date: datetime
    created_at: datetime
    updated_at: datetime
    payments: List[PaymentRecord]
    notes: Optional[str] = None


class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int
    page: int
    size: int


class AccountSearchFilters(BaseModel):
    client_id: Optional[str] = None
    status: Optional[AccountStatus] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


class PaymentSummary(BaseModel):
    total_paid: float
    total_pending: float
    payment_count: int