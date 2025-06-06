from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from bson import ObjectId


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

    @field_validator('id', mode='before')
    @classmethod
    def validate_object_id(cls, v):
        """Convierte ObjectId a string automáticamente"""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        # Encoder para serialización JSON
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


# Modelo para crear cuentas (sin ID)
class AccountCreate(BaseModel):
    account_number: str
    client_id: str
    client_name: str
    client_email: str
    items: List[AccountItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    discount: float = 0.0
    total_amount: float = 0.0
    due_date: datetime
    created_by: str
    notes: Optional[str] = None


# Modelo para actualizar cuentas
class AccountUpdate(BaseModel):
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    items: Optional[List[AccountItem]] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    discount: Optional[float] = None
    total_amount: Optional[float] = None
    status: Optional[AccountStatus] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Modelo para respuestas (garantiza que el ID sea string)
class AccountResponse(BaseModel):
    id: str = Field(..., alias="_id")
    account_number: str
    client_id: str
    client_name: str
    client_email: str
    items: List[AccountItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    discount: float = 0.0
    total_amount: float = 0.0
    status: AccountStatus = AccountStatus.PENDING
    due_date: datetime
    created_at: datetime
    updated_at: datetime
    created_by: str
    payments: List[PaymentRecord] = []
    notes: Optional[str] = None

    @field_validator('id', mode='before')
    @classmethod
    def convert_object_id(cls, v):
        """Asegura que el ID sea siempre string"""
        if isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }