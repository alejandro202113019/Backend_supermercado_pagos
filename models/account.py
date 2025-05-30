from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class ProductCategory(str, Enum):
    FOOD = "food"
    BEVERAGES = "beverages"
    CLEANING = "cleaning"
    PERSONAL_CARE = "personal_care"
    HOME = "home"
    OTHER = "other"


class Product(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    description: Optional[str] = None
    price: float
    category: ProductCategory = ProductCategory.OTHER
    brand: Optional[str] = None
    barcode: Optional[str] = None
    stock: int = 0
    min_stock: int = 0
    status: ProductStatus = ProductStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # User ID
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True