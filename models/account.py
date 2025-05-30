from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AccountStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    CHECK = "check"


class AccountItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float


class PaymentRecord(BaseModel):
    payment_date: datetime
    amount: float
    payment_method: PaymentMethod
    reference: Optional[str] = None
    processed_by: str  # User ID who processed the payment


class Account(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    account_number: str  # Número único de cuenta
    client_id: str  # User ID del cliente
    client_name: str
    client_email: str
    items: List[AccountItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    discount: float = 0.0
    total_amount: float = 0.0
    status: AccountStatus = AccountStatus.PENDING
    due_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID who created the account
    payments: List[PaymentRecord] = []
    notes: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True