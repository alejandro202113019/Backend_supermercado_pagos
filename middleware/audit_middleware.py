import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
from utils.security import get_client_ip


async def get_optional_current_user_from_request(request: Request) -> Optional[dict]:
    """Obtiene el usuario actual si está autenticado, sin requerir autenticación"""
    try:
        from utils.security import verify_token
        
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


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware para registrar automáticamente acciones de auditoría"""
    
    def __init__(self, app, skip_paths: list = None):
        super().__init__(app)
        self.skip_paths = skip_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/favicon.ico",
            "/health"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Saltar paths que no necesitan auditoría
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        # Obtener información del request
        start_time = time.time()
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        method = request.method
        path = request.url.path
        
        # Obtener información del usuario si está autenticado
        user_info = await get_optional_current_user_from_request(request)
        
        # Procesar request
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time
        
        # Determinar si fue exitoso
        success = 200 <= response.status_code < 400
        
        # Registrar en auditoría para ciertos endpoints
        await self._log_request(
            user_info=user_info,
            method=method,
            path=path,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=response.status_code,
            success=success,
            process_time=process_time
        )
        
        return response
    
    async def _log_request(
        self,
        user_info: dict,
        method: str,
        path: str,
        ip_address: str,
        user_agent: str,
        status_code: int,
        success: bool,
        process_time: float
    ):
        """Registra el request en el log de auditoría"""
        
        # Solo auditar ciertos tipos de requests
        audit_paths = {
            "/auth/login": "login",
            "/auth/logout": "logout",
            "/users": "read",
            "/products": "read", 
            "/accounts": "read",
            "/payments": "read"
        }
        
        # Determinar si debe auditarse
        should_audit = False
        action = "read"
        resource = "unknown"
        
        for audit_path, audit_action in audit_paths.items():
            if path.startswith(audit_path):
                should_audit = True
                action = audit_action
                resource = audit_path.split("/")[1]
                break
        
        # Auditar operaciones CRUD con acciones válidas
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            should_audit = True
            if method == "POST":
                action = "create"
            elif method in ["PUT", "PATCH"]:
                action = "update"
            elif method == "DELETE":
                action = "delete"
        
        if should_audit:
            try:
                # Importación diferida para evitar circular imports
                from services.audit_service import audit_service
                
                await audit_service.log_action(
                    user_id=user_info.get("user_id") if user_info else None,
                    username=user_info.get("username") if user_info else "anonymous",
                    action=action,  # Usar solo acciones válidas del enum
                    resource=resource,
                    details={
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "process_time": round(process_time, 3),
                        "user_agent": user_agent[:100] if user_agent else None  # Limitar longitud
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=success,
                    session_id=user_info.get("session_id") if user_info else None
                )
            except Exception as e:
                # No fallar si hay error en auditoría
                print(f"Error en auditoría: {e}")
    
    def _extract_resource_id(self, path: str) -> str:
        """Extrae el ID del recurso de la URL"""
        parts = path.split("/")
        # Buscar partes que parezcan IDs (números o UUIDs)
        for part in parts:
            if part and (part.isdigit() or len(part) == 24):  # ObjectId tiene 24 caracteres
                return part
        return None