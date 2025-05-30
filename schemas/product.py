from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from models.product import ProductStatus, ProductCategory


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    category: ProductCategory = ProductCategory.OTHER
    brand: Optional[str] = None
    barcode: Optional[str] = None
    stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category: Optional[ProductCategory] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    status: Optional[ProductStatus] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    category: ProductCategory
    brand: Optional[str] = None
    barcode: Optional[str] = None
    stock: int
    min_stock: int
    status: ProductStatus
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int
    page: int
    size: int


class ProductSearchFilters(BaseModel):
    name: Optional[str] = None
    category: Optional[ProductCategory] = None
    brand: Optional[str] = None
    status: Optional[ProductStatus] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None