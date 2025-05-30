from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, 
    ProductListResponse, ProductSearchFilters
)
from services.product_service import product_service
from middleware.auth_middleware import require_admin, get_current_active_user
from models.product import ProductStatus, ProductCategory
from utils.security import get_client_ip
from utils.exceptions import ValidationException, NotFoundException


router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse)
async def create_product(
    request: Request,
    product_data: ProductCreate,
    current_user = Depends(require_admin)
):
    """Crea un nuevo producto (solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        product = await product_service.create_product(
            product_data,
            str(current_user.id),
            ip_address
        )
        
        return ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            brand=product.brand,
            barcode=product.barcode,
            stock=product.stock,
            min_stock=product.min_stock,
            status=product.status,
            created_at=product.created_at,
            updated_at=product.updated_at
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    name: Optional[str] = None,
    category: Optional[ProductCategory] = None,
    brand: Optional[str] = None,
    status: Optional[ProductStatus] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    current_user = Depends(get_current_active_user)
):
    """Obtiene lista de productos con paginación y filtros"""
    try:
        # Crear filtros
        filters = ProductSearchFilters(
            name=name,
            category=category,
            brand=brand,
            status=status,
            min_price=min_price,
            max_price=max_price
        )
        
        result = await product_service.get_products(
            page=page,
            size=size,
            filters=filters
        )
        
        return ProductListResponse(
            products=result["products"],
            total=result["total"],
            page=result["page"],
            size=result["size"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/active", response_model=list[ProductResponse])
async def get_active_products(current_user = Depends(get_current_active_user)):
    """Obtiene todos los productos activos"""
    try:
        products = await product_service.get_active_products()
        return products
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    current_user = Depends(get_current_active_user)
):
    """Obtiene un producto por ID"""
    try:
        product = await product_service.get_product_by_id(product_id)
        
        return ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            brand=product.brand,
            barcode=product.barcode,
            stock=product.stock,
            min_stock=product.min_stock,
            status=product.status,
            created_at=product.created_at,
            updated_at=product.updated_at
        )
        
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    request: Request,
    product_id: str,
    product_data: ProductUpdate,
    current_user = Depends(require_admin)
):
    """Actualiza un producto (solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        product = await product_service.update_product(
            product_id,
            product_data,
            str(current_user.id),
            ip_address
        )
        
        return ProductResponse(
            id=str(product.id),
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            brand=product.brand,
            barcode=product.barcode,
            stock=product.stock,
            min_stock=product.min_stock,
            status=product.status,
            created_at=product.created_at,
            updated_at=product.updated_at
        )
        
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{product_id}")
async def delete_product(
    request: Request,
    product_id: str,
    current_user = Depends(require_admin)
):
    """Elimina un producto (soft delete, solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        success = await product_service.delete_product(
            product_id,
            str(current_user.id),
            ip_address
        )
        
        if success:
            return {"message": "Producto eliminado exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al eliminar producto"
            )
            
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.patch("/{product_id}/stock")
async def update_product_stock(
    request: Request,
    product_id: str,
    quantity_change: int,
    current_user = Depends(require_admin)
):
    """Actualiza el stock de un producto (solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        product = await product_service.update_stock(
            product_id,
            quantity_change,
            str(current_user.id),
            ip_address,
            operation="manual_adjustment"
        )
        
        return {
            "message": f"Stock actualizado. Nuevo stock: {product.stock}",
            "product_id": str(product.id),
            "new_stock": product.stock
        }
        
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )