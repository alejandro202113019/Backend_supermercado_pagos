from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "supermarket_payments"
    
    # JWT
    secret_key: str = "default-secret-key-change-in-production-32-characters-long"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Encryption
    encryption_key: str = "default-encryption-key-32-chars"
    
    # App
    debug: bool = True
    app_name: str = "Supermarket Payment System"
    version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Verificar configuraciones críticas
        if self.secret_key == "default-secret-key-change-in-production-32-characters-long":
            print("⚠️  ADVERTENCIA: Usando clave secreta por defecto. Cambiar en producción!")
        
        if self.encryption_key == "default-encryption-key-32-chars":
            print("⚠️  ADVERTENCIA: Usando clave de cifrado por defecto. Cambiar en producción!")
        
        if "localhost" in self.mongodb_url:
            print("⚠️  ADVERTENCIA: Usando MongoDB local. Configurar MongoDB Atlas en producción!")


# Crear instancia de configuración con manejo de errores
try:
    settings = Settings()
    print("✅ Configuración cargada correctamente")
except Exception as e:
    print(f"❌ Error cargando configuración: {e}")
    print("🔧 Creando configuración por defecto...")
    
    # Configuración de emergencia
    class DefaultSettings:
        mongodb_url = "mongodb://localhost:27017"
        database_name = "supermarket_payments"
        secret_key = "emergency-secret-key-32-characters-long-please-change"
        algorithm = "HS256"
        access_token_expire_minutes = 30
        encryption_key = "emergency-encryption-key-32-chars"
        debug = True
        app_name = "Supermarket Payment System"
        version = "1.0.0"
    
    settings = DefaultSettings()
    print("⚠️  Usando configuración de emergencia - revisa tu archivo .env")