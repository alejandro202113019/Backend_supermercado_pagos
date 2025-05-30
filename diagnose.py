#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas en la aplicación
"""

import os
import sys
import importlib.util

def check_file_exists(file_path):
    """Verifica si un archivo existe"""
    if os.path.exists(file_path):
        print(f"✅ {file_path}")
        return True
    else:
        print(f"❌ {file_path} - NO EXISTE")
        return False

def check_import(module_name, description=""):
    """Verifica si un módulo se puede importar"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} {description}")
        return True
    except Exception as e:
        print(f"❌ {module_name} {description} - ERROR: {e}")
        return False

def main():
    """Función principal de diagnóstico"""
    
    print("🔧 DIAGNÓSTICO DEL SISTEMA")
    print("=" * 50)
    
    # 1. Verificar estructura de archivos
    print("\n📁 VERIFICANDO ESTRUCTURA DE ARCHIVOS:")
    files_to_check = [
        "app.py",
        "config/__init__.py",
        "config/settings.py", 
        "config/database.py",
        "models/__init__.py",
        "models/user.py",
        "models/product.py", 
        "models/account.py",
        "models/audit.py",
        "services/__init__.py",
        "services/auth_service.py",
        "services/user_service.py",
        "services/product_service.py",
        "services/account_service.py",
        "services/audit_service.py",
        "services/encryption_service.py",
        "routers/__init__.py",
        "routers/auth.py",
        "routers/users.py",
        "routers/products.py",
        "routers/accounts.py",
        "middleware/__init__.py",
        "middleware/auth_middleware.py",
        "middleware/audit_middleware.py",
        "middleware/security_middleware.py",
        "schemas/__init__.py",
        "schemas/auth.py",
        "schemas/user.py",
        "schemas/product.py",
        "schemas/account.py",
        "schemas/audit.py",
        "utils/__init__.py",
        "utils/security.py",
        "utils/validators.py",
        "utils/exceptions.py"
    ]
    
    all_files_exist = True
    for file_path in files_to_check:
        if not check_file_exists(file_path):
            all_files_exist = False
    
    # 2. Verificar dependencias
    print("\n📦 VERIFICANDO DEPENDENCIAS:")
    dependencies = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("pydantic_settings", "Settings management"),
        ("motor", "MongoDB async driver"),
        ("pymongo", "MongoDB driver"),
        ("jose", "JWT handling (python-jose)"),  # Corregido: jose en lugar de python_jose
        ("passlib", "Password hashing"),
        ("cryptography", "Encryption"),
        ("dotenv", "Environment variables (python-dotenv)")  # Corregido: dotenv en lugar de python_dotenv
    ]
    
    all_deps_ok = True
    for dep, desc in dependencies:
        if not check_import(dep, f"- {desc}"):
            all_deps_ok = False
    
    # 3. Verificar configuración
    print("\n⚙️  VERIFICANDO CONFIGURACIÓN:")
    try:
        from config.settings import settings
        print(f"✅ Configuración cargada")
        print(f"   📊 Base de datos: {settings.database_name}")
        print(f"   🔗 MongoDB URL: {settings.mongodb_url[:50]}...")
        print(f"   🐛 Debug: {settings.debug}")
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        all_deps_ok = False
    
    # 4. Verificar modelos
    print("\n🏗️  VERIFICANDO MODELOS:")
    models_ok = True
    try:
        from models.user import User, UserRole, UserStatus
        print("✅ Modelo User")
    except Exception as e:
        print(f"❌ Modelo User: {e}")
        models_ok = False
    
    try:
        from models.product import Product, ProductStatus, ProductCategory
        print("✅ Modelo Product")
    except Exception as e:
        print(f"❌ Modelo Product: {e}")
        models_ok = False
    
    try:
        from models.account import Account, AccountStatus, PaymentMethod
        print("✅ Modelo Account")
    except Exception as e:
        print(f"❌ Modelo Account: {e}")
        models_ok = False
    
    try:
        from models.audit import AuditLog, SessionLog, AuditAction
        print("✅ Modelo Audit")
    except Exception as e:
        print(f"❌ Modelo Audit: {e}")
        models_ok = False
    
    # 5. Verificar servicios
    print("\n🔧 VERIFICANDO SERVICIOS:")
    services_ok = True
    services = [
        "services.auth_service",
        "services.user_service", 
        "services.product_service",
        "services.account_service",
        "services.audit_service",
        "services.encryption_service"
    ]
    
    for service in services:
        if not check_import(service):
            services_ok = False
    
    # 6. Verificar routers
    print("\n🛣️  VERIFICANDO ROUTERS:")
    routers_ok = True
    routers = [
        "routers.auth",
        "routers.users",
        "routers.products", 
        "routers.accounts"
    ]
    
    for router in routers:
        if not check_import(router):
            routers_ok = False
    
    # 7. Verificar imports críticos específicos
    print("\n🔍 VERIFICANDO IMPORTS CRÍTICOS:")
    critical_imports_ok = True
    
    try:
        from jose import jwt
        print("✅ JWT functionality (jose.jwt)")
    except Exception as e:
        print(f"❌ JWT functionality: {e}")
        critical_imports_ok = False
    
    try:
        from dotenv import load_dotenv
        print("✅ Environment loading (dotenv.load_dotenv)")
    except Exception as e:
        print(f"❌ Environment loading: {e}")
        critical_imports_ok = False
    
    try:
        from passlib.context import CryptContext
        print("✅ Password hashing (passlib.context)")
    except Exception as e:
        print(f"❌ Password hashing: {e}")
        critical_imports_ok = False
    
    try:
        from cryptography.fernet import Fernet
        print("✅ Encryption (cryptography.fernet)")
    except Exception as e:
        print(f"❌ Encryption: {e}")
        critical_imports_ok = False
    
    # 8. Resumen
    print("\n" + "="*50)
    print("📋 RESUMEN DEL DIAGNÓSTICO:")
    
    if all_files_exist:
        print("✅ Estructura de archivos: OK")
    else:
        print("❌ Estructura de archivos: FALTAN ARCHIVOS")
    
    if all_deps_ok:
        print("✅ Dependencias básicas: OK")
    else:
        print("❌ Dependencias básicas: FALTAN PAQUETES")
    
    if critical_imports_ok:
        print("✅ Imports críticos: OK")
    else:
        print("❌ Imports críticos: ERRORES")
    
    if models_ok:
        print("✅ Modelos: OK")
    else:
        print("❌ Modelos: ERRORES")
    
    if services_ok:
        print("✅ Servicios: OK")
    else:
        print("❌ Servicios: ERRORES")
    
    if routers_ok:
        print("✅ Routers: OK")
    else:
        print("❌ Routers: ERRORES")
    
    print("\n🎯 RECOMENDACIONES:")
    
    if not all_files_exist:
        print("1. Crear los archivos faltantes de la estructura")
    
    if not all_deps_ok:
        print("2. Instalar dependencias: pip install -r requirements.txt")
    
    if not critical_imports_ok:
        print("3. Revisar instalación de paquetes críticos")
    
    if not (models_ok and services_ok and routers_ok):
        print("4. Revisar y corregir errores de importación")
        print("5. Verificar que el archivo .env existe y está configurado")
    
    overall_ok = (all_files_exist and all_deps_ok and critical_imports_ok and 
                  models_ok and services_ok and routers_ok)
    
    if overall_ok:
        print("\n🎉 ¡TODO ESTÁ PERFECTO!")
        print("🚀 Puedes ejecutar: python app_simple.py")
        print("🔧 O inicializar la DB: python init_db.py")
    else:
        print("\n🔧 Hay algunos problemas que necesitan corrección")

if __name__ == "__main__":
    main()