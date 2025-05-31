from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import time
import traceback

# Importar configuración y base de datos
from config.settings import settings
from config.database import connect_to_mongo, close_mongo_connection

# Importar routers
from routers import auth, users, products, accounts

# Importar middleware
from middleware.audit_middleware import AuditMiddleware
from middleware.security_middleware import SecurityMiddleware, RateLimitMiddleware

# Importar excepciones personalizadas
from utils.exceptions import (
    CustomException, AuthenticationException, AuthorizationException,
    NotFoundException, ValidationException, DatabaseException
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    # Startup
    print("Iniciando aplicación...")
    await connect_to_mongo()
    yield
    # Shutdown
    print("Cerrando aplicación...")
    await close_mongo_connection()


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Sistema de gestión de pagos de cuentas pendientes para supermercado",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agregar middleware de seguridad
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, time_window=60)
app.add_middleware(AuditMiddleware)


# Manejadores de excepciones globales
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "type": "custom_error"}
    )


@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.message, "type": "authentication_error"},
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message, "type": "authorization_error"}
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "type": "not_found_error"}
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.message, "type": "validation_error"}
    )


@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error en la base de datos", "type": "database_error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador para excepciones no capturadas"""
    print(f"🚨 ERROR NO MANEJADO: {exc}")
    print(f"📍 Path: {request.url.path}")
    print(f"🔍 Traceback completo:")
    traceback.print_exc()
    
    if settings.debug:
        error_detail = f"Error interno: {str(exc)}\n{traceback.format_exc()}"
    else:
        error_detail = "Error interno del servidor"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_detail, "type": "internal_error"}
    )


# Incluir routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(accounts.router)


# Endpoints básicos
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema de Gestión de Pagos - Supermercado",
        "version": settings.version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    current_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "status": "healthy",
        "timestamp": current_time,
        "version": settings.version
    }


# Endpoint para obtener información de la API
@app.get("/info")
async def api_info():
    """Información de la API"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": "development" if settings.debug else "production",
        "features": [
            "Autenticación JWT",
            "Gestión de usuarios",
            "Gestión de productos", 
            "Gestión de cuentas",
            "Procesamiento de pagos",
            "Auditoría completa",
            "Cifrado de datos sensibles",
            "Validación de políticas de contraseña"
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )