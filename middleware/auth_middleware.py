from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from utils.security import verify_token
from utils.exceptions import AuthenticationException, AuthorizationException
from models.user import UserRole


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el usuario actual desde el token JWT"""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            raise AuthenticationException("Token inválido")
        
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationException("Token inválido")
        
        # Importación diferida para evitar circular imports
        from services.auth_service import auth_service
        
        # Obtener usuario de la base de datos
        user = await auth_service.get_current_user(user_id)
        
        # Actualizar actividad de sesión si existe session_id
        session_id = payload.get("session_id")
        if session_id:
            from services.audit_service import audit_service
            await audit_service.update_session_activity(session_id)
        
        return user
        
    except Exception as e:
        if isinstance(e, (AuthenticationException, AuthorizationException)):
            raise e
        raise AuthenticationException("Error de autenticación")


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Verifica que el usuario esté activo"""
    if current_user.status != "active":
        raise AuthenticationException("Usuario inactivo")
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Decorator para requerir roles específicos"""
    def role_checker(current_user = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise AuthorizationException("Permisos insuficientes")
        return current_user
    return role_checker


# Funciones de conveniencia para roles específicos
async def require_admin(current_user = Depends(require_role([UserRole.ADMIN]))):
    """Requiere rol de administrador"""
    return current_user


async def require_admin_or_client(current_user = Depends(require_role([UserRole.ADMIN, UserRole.CLIENT]))):
    """Requiere rol de administrador o cliente"""
    return current_user


# Middleware para obtener información del usuario sin requerir autenticación
async def get_optional_current_user(request: Request) -> Optional[dict]:
    """Obtiene el usuario actual si está autenticado, sin requerir autenticación"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        
        if payload is None:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "session_id": payload.get("session_id")
        }
    except Exception:
        return None