from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    ChangePasswordRequest
)
from services.auth_service import auth_service
from services.audit_service import audit_service
from middleware.auth_middleware import get_current_active_user, security
from utils.security import get_client_ip
from utils.exceptions import AuthenticationException, ValidationException
from config.settings import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """Autentica un usuario y retorna un token JWT"""
    try:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        
        user, access_token = await auth_service.authenticate_user(
            login_data, ip_address, user_agent
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            username=user.username,
            role=user.role,
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/register", response_model=RegisterResponse)
async def register(request: Request, register_data: RegisterRequest):
    """Registra un nuevo usuario (solo para administradores en producción)"""
    try:
        ip_address = get_client_ip(request)
        
        user = await auth_service.register_user(register_data, ip_address)
        
        return RegisterResponse(
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            message="Usuario registrado exitosamente"
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


@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user = Depends(get_current_active_user)
):
    """Cierra la sesión del usuario"""
    try:
        from utils.security import verify_token
        
        ip_address = get_client_ip(request)
        token = credentials.credentials
        payload = verify_token(token)
        session_id = payload.get("session_id") if payload else None
        
        if session_id:
            await audit_service.log_logout(
                user_id=str(current_user.id),
                username=current_user.username,
                session_id=session_id,
                ip_address=ip_address
            )
        
        return {"message": "Sesión cerrada exitosamente"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cerrar sesión"
        )


@router.post("/change-password")
async def change_password(
    request: Request,
    change_data: ChangePasswordRequest,
    current_user = Depends(get_current_active_user)
):
    """Cambia la contraseña del usuario actual"""
    try:
        ip_address = get_client_ip(request)
        
        success = await auth_service.change_password(
            str(current_user.id),
            change_data,
            ip_address
        )
        
        if success:
            return {"message": "Contraseña cambiada exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al cambiar la contraseña"
            )
            
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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


@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """Obtiene información del usuario actual"""
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "status": current_user.status,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


@router.get("/sessions")
async def get_active_sessions(current_user = Depends(get_current_active_user)):
    """Obtiene las sesiones activas del usuario actual"""
    try:
        sessions = await audit_service.get_active_sessions(str(current_user.id))
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener sesiones"
        )