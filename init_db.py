#!/usr/bin/env python3
"""
Script simple para inicializar la base de datos y crear un usuario admin
"""

import asyncio
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def init_database():
    """Inicializa la base de datos y crea usuario admin"""
    
    try:
        # Importar después de cargar las variables de entorno
        from motor.motor_asyncio import AsyncIOMotorClient
        from utils.security import get_password_hash
        from services.encryption_service import encryption_service
        from config.settings import settings
        
        print("🔧 Inicializando base de datos...")
        print(f"📊 Base de datos: {settings.database_name}")
        
        # Conectar a MongoDB
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Probar conexión
        await client.admin.command('ping')
        print("✅ Conexión a MongoDB exitosa!")
        
        # Crear usuario admin si no existe
        admin_email = "admin@supermarket.com"
        existing_admin = await db.users.find_one({"email": admin_email})
        
        if not existing_admin:
            print("📝 Creando usuario administrador inicial...")
            
            admin_user = {
                "email": admin_email,
                "username": "admin",
                "full_name": "Administrador del Sistema",
                "phone": "1234567890",
                "address": "Oficina Principal",
                "role": "admin",
                "status": "active",
                "hashed_password": get_password_hash("Admin123!"),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "failed_login_attempts": 0,
                "password_changed_at": "2024-01-01T00:00:00"
            }
            
            # Cifrar campos sensibles
            admin_user = encryption_service.encrypt_sensitive_fields(
                admin_user, 
                ["phone", "address"]
            )
            
            result = await db.users.insert_one(admin_user)
            print(f"✅ Usuario administrador creado con ID: {result.inserted_id}")
            print(f"📧 Email: {admin_email}")
            print(f"🔑 Contraseña: Admin123!")
        else:
            print("ℹ️  Usuario administrador ya existe")
        
        await client.close()
        print("🎉 Inicialización completada!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(init_database())
    if success:
        print("\n✅ Base de datos lista!")
        print("🚀 Para iniciar el servidor ejecuta: python app.py")
    else:
        print("\n❌ Error en la inicialización")
        print("🔧 Revisa tu archivo .env y la conexión a MongoDB")