from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from services.user_service import user_service
from middleware.auth_middleware import require_admin, get_current_active_user
from models.user import UserRole, UserStatus
from utils.security import get_client_ip
from utils.exceptions import ValidationException, NotFoundException


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user = Depends(require_admin)
):
    """Crea un nuevo usuario (solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        user = await user_service.create_user(
            user_data,
            str(current_user.id),
            ip_address
        )
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            phone=user.phone,
            address=user.address,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            last_login=user.last_login
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


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    current_user = Depends(require_admin)
):
    """Obtiene lista de usuarios con paginación y filtros (solo administradores)"""
    try:
        result = await user_service.get_users(
            page=page,
            size=size,
            role=role,
            status=status,
            search=search
        )
        
        return UserListResponse(
            users=result["users"],
            total=result["total"],
            page=result["page"],
            size=result["size"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/clients", response_model=list[UserResponse])
async def get_clients(current_user = Depends(require_admin)):
    """Obtiene lista de todos los clientes activos (solo administradores)"""
    try:
        clients = await user_service.get_clients()
        return clients
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user = Depends(get_current_active_user)
):
    """Obtiene un usuario por ID"""
    try:
        # Los clientes solo pueden ver su propia información
        if current_user.role == UserRole.CLIENT and str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver este usuario"
            )
        
        user = await user_service.get_user_by_id(user_id)
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            phone=user.phone,
            address=user.address,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            last_login=user.last_login
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


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: str,
    user_data: UserUpdate,
    current_user = Depends(get_current_active_user)
):
    """Actualiza un usuario"""
    try:
        ip_address = get_client_ip(request)
        
        # Los clientes solo pueden actualizar su propia información (sin cambiar rol/status)
        if current_user.role == UserRole.CLIENT:
            if str(current_user.id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para actualizar este usuario"
                )
            
            # Los clientes no pueden cambiar su rol o status
            if user_data.role is not None or user_data.status is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puedes cambiar tu rol o status"
                )
        
        user = await user_service.update_user(
            user_id,
            user_data,
            str(current_user.id),
            ip_address
        )
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            phone=user.phone,
            address=user.address,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            last_login=user.last_login
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


@router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: str,
    current_user = Depends(require_admin)
):
    """Elimina un usuario (soft delete, solo administradores)"""
    try:
        ip_address = get_client_ip(request)
        
        # No permitir que un admin se elimine a sí mismo
        if str(current_user.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propia cuenta"
            )
        
        success = await user_service.delete_user(
            user_id,
            str(current_user.id),
            ip_address
        )
        
        if success:
            return {"message": "Usuario eliminado exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al eliminar usuario"
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