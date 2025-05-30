from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from schemas.account import (
    AccountCreate, AccountUpdate, PaymentRequest, AccountResponse,
    AccountListResponse, AccountSearchFilters
)
from services.account_service import account_service
from middleware.auth_middleware import require_admin, get_current_active_user
from models.user import UserRole
from models.account import AccountStatus
from utils.security import get_client_ip
from utils.exceptions import ValidationException, NotFoundException


router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse)
async def create_account(
    request: Request,
    account_data: AccountCreate,
    current_user = Depends(require_admin)
):
    """Crea una nueva cuenta pendiente (solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        account = await account_service.create_account(
            account_data,
            str(current_user.id),
            ip_address
        )
        
        return AccountResponse(
            id=str(account.id),
            account_number=account.account_number,
            client_id=account.client_id,
            client_name=account.client_name,
            client_email=account.client_email,
            items=account.items,
            subtotal=account.subtotal,
            tax=account.tax,
            discount=account.discount,
            total_amount=account.total_amount,
            status=account.status,
            due_date=account.due_date,
            created_at=account.created_at,
            updated_at=account.updated_at,
            payments=account.payments,
            notes=account.notes
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/", response_model=AccountListResponse)
async def get_accounts(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    client_id: Optional[str] = None,
    status: Optional[AccountStatus] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    current_user = Depends(get_current_active_user)
):
    """Obtiene lista de cuentas con paginación y filtros"""
    try:
        # Los clientes solo pueden ver sus propias cuentas
        if current_user.role == UserRole.CLIENT:
            client_id = str(current_user.id)
        
        # Crear filtros
        filters = AccountSearchFilters(
            client_id=client_id,
            status=status,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        result = await account_service.get_accounts(
            page=page,
            size=size,
            filters=filters
        )
        
        return AccountListResponse(
            accounts=result["accounts"],
            total=result["total"],
            page=result["page"],
            size=result["size"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/my-accounts", response_model=AccountListResponse)
async def get_my_accounts(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[AccountStatus] = None,
    current_user = Depends(get_current_active_user)
):
    """Obtiene las cuentas del usuario actual (solo clientes)"""
    try:
        if current_user.role != UserRole.CLIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los clientes pueden usar este endpoint"
            )
        
        result = await account_service.get_client_accounts(
            str(current_user.id),
            page=page,
            size=size,
            status=status
        )
        
        return AccountListResponse(
            accounts=result["accounts"],
            total=result["total"],
            page=result["page"],
            size=result["size"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user = Depends(get_current_active_user)
):
    """Obtiene una cuenta por ID"""
    try:
        account = await account_service.get_account_by_id(account_id)
        
        # Los clientes solo pueden ver sus propias cuentas
        if current_user.role == UserRole.CLIENT and account.client_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver esta cuenta"
            )
        
        return AccountResponse(
            id=str(account.id),
            account_number=account.account_number,
            client_id=account.client_id,
            client_name=account.client_name,
            client_email=account.client_email,
            items=account.items,
            subtotal=account.subtotal,
            tax=account.tax,
            discount=account.discount,
            total_amount=account.total_amount,
            status=account.status,
            due_date=account.due_date,
            created_at=account.created_at,
            updated_at=account.updated_at,
            payments=account.payments,
            notes=account.notes
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


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    request: Request,
    account_id: str,
    account_data: AccountUpdate,
    current_user = Depends(require_admin)
):
    """Actualiza una cuenta (solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        account = await account_service.update_account(
            account_id,
            account_data,
            str(current_user.id),
            ip_address
        )
        
        return AccountResponse(
            id=str(account.id),
            account_number=account.account_number,
            client_id=account.client_id,
            client_name=account.client_name,
            client_email=account.client_email,
            items=account.items,
            subtotal=account.subtotal,
            tax=account.tax,
            discount=account.discount,
            total_amount=account.total_amount,
            status=account.status,
            due_date=account.due_date,
            created_at=account.created_at,
            updated_at=account.updated_at,
            payments=account.payments,
            notes=account.notes
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


@router.post("/{account_id}/payment", response_model=AccountResponse)
async def process_payment(
    request: Request,
    account_id: str,
    payment_data: PaymentRequest,
    current_user = Depends(get_current_active_user)
):
    """Procesa un pago para una cuenta"""
    try:
        ip_address = get_client_ip(request)
        
        # Verificar permisos: el cliente solo puede pagar sus propias cuentas
        if current_user.role == UserRole.CLIENT:
            account = await account_service.get_account_by_id(account_id)
            if account.client_id != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para pagar esta cuenta"
                )
        
        account = await account_service.process_payment(
            account_id,
            payment_data,
            str(current_user.id),
            ip_address
        )
        
        return AccountResponse(
            id=str(account.id),
            account_number=account.account_number,
            client_id=account.client_id,
            client_name=account.client_name,
            client_email=account.client_email,
            items=account.items,
            subtotal=account.subtotal,
            tax=account.tax,
            discount=account.discount,
            total_amount=account.total_amount,
            status=account.status,
            due_date=account.due_date,
            created_at=account.created_at,
            updated_at=account.updated_at,
            payments=account.payments,
            notes=account.notes
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


@router.delete("/{account_id}")
async def delete_account(
    request: Request,
    account_id: str,
    current_user = Depends(require_admin)
):
    """Elimina una cuenta (solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        success = await account_service.delete_account(
            account_id,
            str(current_user.id),
            ip_address
        )
        
        if success:
            return {"message": "Cuenta eliminada exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al eliminar cuenta"
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


@router.get("/summary/payments")
async def get_payment_summary(
    current_user = Depends(get_current_active_user)
):
    """Obtiene resumen de pagos"""
    try:
        # Los clientes solo pueden ver su propio resumen
        client_id = str(current_user.id) if current_user.role == UserRole.CLIENT else None
        
        summary = await account_service.get_payment_summary(client_id)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/mark-overdue")
async def mark_overdue_accounts(
    request: Request,
    current_user = Depends(require_admin)
):
    """Marca cuentas vencidas como overdue (solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        updated_count = await account_service.mark_overdue_accounts(ip_address)
        
        return {
            "message": f"Se marcaron {updated_count} cuentas como vencidas",
            "updated_accounts": updated_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )