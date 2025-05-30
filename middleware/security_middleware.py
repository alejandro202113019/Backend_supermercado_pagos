import json
import time
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from utils.validators import sanitize_string


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware para aplicar medidas de seguridad"""
    
    def __init__(self, app):
        super().__init__(app)
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.blocked_patterns = [
            "script>", "<script", "javascript:", "vbscript:",
            "onload=", "onerror=", "onclick=", "eval(",
            "document.cookie", "document.write"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar tamaño del request
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request demasiado grande"
            )
        
        # Validar headers de seguridad
        self._validate_security_headers(request)
        
        # Sanitizar datos del request si es necesario
        await self._sanitize_request_data(request)
        
        # Procesar request
        response = await call_next(request)
        
        # Agregar headers de seguridad a la respuesta
        self._add_security_headers(response)
        
        return response
    
    def _validate_security_headers(self, request: Request):
        """Valida headers de seguridad del request"""
        
        # Validar User-Agent (prevenir requests automatizados maliciosos)
        user_agent = request.headers.get("user-agent", "")
        suspicious_agents = ["sqlmap", "nikto", "nmap", "masscan", "bot"]
        
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request bloqueado por medidas de seguridad"
            )
        
        # Validar Content-Type para requests con body
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if content_type and not any(ct in content_type.lower() for ct in [
                "application/json", "application/x-www-form-urlencoded", 
                "multipart/form-data", "text/plain"
            ]):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Content-Type no soportado"
                )
    
    async def _sanitize_request_data(self, request: Request):
        """Sanitiza datos del request para prevenir inyecciones"""
        
        # Solo sanitizar para ciertos content-types
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            try:
                # Leer el body
                body = await request.body()
                if body:
                    # Parsear JSON
                    data = json.loads(body.decode('utf-8'))
                    
                    # Sanitizar recursivamente
                    sanitized_data = self._sanitize_json_data(data)
                    
                    # Reemplazar el body con datos sanitizados
                    request._body = json.dumps(sanitized_data).encode('utf-8')
                    
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Si no se puede parsear, dejar como está
                pass
    
    def _sanitize_json_data(self, data):
        """Sanitiza datos JSON recursivamente"""
        if isinstance(data, dict):
            return {key: self._sanitize_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        elif isinstance(data, str):
            # Verificar patrones maliciosos
            data_lower = data.lower()
            for pattern in self.blocked_patterns:
                if pattern in data_lower:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Contenido bloqueado por medidas de seguridad"
                    )
            
            # Sanitizar string
            return sanitize_string(data)
        else:
            return data
    
    def _add_security_headers(self, response: Response):
        """Agrega headers de seguridad a la respuesta"""
        
        # Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevenir MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Activar XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Contenido de seguridad estricto
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Forzar HTTPS (en producción)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        
        # Política de referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Política de permisos
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware simple para rate limiting"""
    
    def __init__(self, app, max_requests: int = 100, time_window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"
        
        # Limpiar contadores antiguos
        current_time = int(time.time())
        self._cleanup_old_entries(current_time)
        
        # Verificar límite de rate
        if self._is_rate_limited(client_ip, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas solicitudes. Intenta de nuevo más tarde."
            )
        
        # Procesar request
        return await call_next(request)
    
    def _is_rate_limited(self, client_ip: str, current_time: int) -> bool:
        """Verifica si la IP está limitada por rate limiting"""
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Agregar timestamp actual
        self.request_counts[client_ip].append(current_time)
        
        # Filtrar requests en la ventana de tiempo
        window_start = current_time - self.time_window
        recent_requests = [
            timestamp for timestamp in self.request_counts[client_ip]
            if timestamp > window_start
        ]
        
        # Actualizar contador
        self.request_counts[client_ip] = recent_requests
        
        # Verificar si excede el límite
        return len(recent_requests) > self.max_requests
    
    def _cleanup_old_entries(self, current_time: int):
        """Limpia entradas antiguas para liberar memoria"""
        window_start = current_time - self.time_window
        
        for ip in list(self.request_counts.keys()):
            # Filtrar requests recientes
            recent_requests = [
                timestamp for timestamp in self.request_counts[ip]
                if timestamp > window_start
            ]
            
            if recent_requests:
                self.request_counts[ip] = recent_requests
            else:
                # Eliminar IP si no tiene requests recientes
                del self.request_counts[ip]