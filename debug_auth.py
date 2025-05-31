#!/usr/bin/env python3
"""
Script para debuggear el problema de autenticación
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
from services.encryption_service import encryption_service
from utils.security import verify_password
import traceback

async def debug_auth():
    """Debug del sistema de autenticación"""
    
    print("🔍 DEBUGGING AUTENTICACIÓN")
    print("=" * 50)
    
    try:
        # 1. Probar conexión a MongoDB
        print("1️⃣ Probando conexión a MongoDB...")
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        await client.admin.command('ping')
        print("   ✅ Conexión exitosa")
        
        # 2. Buscar usuario admin
        print("\n2️⃣ Buscando usuario admin...")
        admin_user = await db.users.find_one({"email": "admin@supermarket.com"})
        
        if not admin_user:
            print("   ❌ Usuario admin no encontrado")
            client.close()
            return False
        
        print("   ✅ Usuario admin encontrado")
        print(f"   📧 Email: {admin_user.get('email')}")
        print(f"   👤 Username: {admin_user.get('username')}")
        print(f"   🔑 Role: {admin_user.get('role')}")
        print(f"   📊 Status: {admin_user.get('status')}")
        print(f"   🆔 ID type: {type(admin_user.get('_id'))}")
        print(f"   🆔 ID value: {admin_user.get('_id')}")
        
        # 3. Probar descifrado
        print("\n3️⃣ Probando descifrado de campos...")
        try:
            decrypted_user = encryption_service.decrypt_sensitive_fields(
                admin_user.copy(), 
                ["phone", "address"]
            )
            print("   ✅ Descifrado exitoso")
            print(f"   📞 Phone: {decrypted_user.get('phone')}")
            print(f"   🏠 Address: {decrypted_user.get('address')}")
        except Exception as e:
            print(f"   ❌ Error en descifrado: {e}")
        
        # 4. Probar verificación de contraseña
        print("\n4️⃣ Probando verificación de contraseña...")
        try:
            password_check = verify_password("Admin123!", admin_user.get('hashed_password'))
            print(f"   {'✅' if password_check else '❌'} Verificación de contraseña: {password_check}")
        except Exception as e:
            print(f"   ❌ Error verificando contraseña: {e}")
        
        # 5. Probar creación del modelo User
        print("\n5️⃣ Probando creación del modelo User...")
        try:
            from models.user import User
            from bson import ObjectId
            
            # Preparar documento
            user_doc = admin_user.copy()
            if isinstance(user_doc['_id'], ObjectId):
                user_doc['_id'] = str(user_doc['_id'])
            
            user_doc = encryption_service.decrypt_sensitive_fields(
                user_doc, 
                ["phone", "address"]
            )
            
            user = User(**user_doc)
            print("   ✅ Modelo User creado exitosamente")
            print(f"   🆔 User ID: {user.id}")
            print(f"   👤 Username: {user.username}")
            print(f"   📊 Status: {user.status}")
        except Exception as e:
            print(f"   ❌ Error creando modelo User: {e}")
            traceback.print_exc()
        
        # 6. Probar configuración de database
        print("\n6️⃣ Probando configuración de database...")
        try:
            from config.database import get_database, connect_to_mongo
            
            # Primero conectar
            await connect_to_mongo()
            
            # Luego obtener database
            test_db = await get_database()
            print(f"   ✅ Database obtenida: {test_db is not None}")
            print(f"   📊 Database name: {test_db.name if test_db else 'None'}")
        except Exception as e:
            print(f"   ❌ Error en configuración de database: {e}")
            traceback.print_exc()
        
        # 7. Probar servicio de auditoría
        print("\n7️⃣ Probando servicio de auditoría...")
        try:
            from services.audit_service import audit_service
            
            # Probar log simple
            await audit_service.log_action(
                user_id="test",
                username="test",
                action="login",
                resource="auth",
                ip_address="127.0.0.1"
            )
            print("   ✅ Servicio de auditoría funciona")
        except Exception as e:
            print(f"   ❌ Error en servicio de auditoría: {e}")
            traceback.print_exc()
        
        # 8. Probar autenticación completa
        print("\n8️⃣ Probando autenticación completa...")
        try:
            from services.auth_service import auth_service
            from schemas.auth import LoginRequest
            
            login_data = LoginRequest(
                email="admin@supermarket.com",
                password="Admin123!"
            )
            
            user, token = await auth_service.authenticate_user(
                login_data, 
                "127.0.0.1", 
                "debug-script"
            )
            
            print("   ✅ Autenticación exitosa!")
            print(f"   🎫 Token generado: {token[:50]}...")
            print(f"   👤 Usuario autenticado: {user.username}")
            
        except Exception as e:
            print(f"   ❌ Error en autenticación: {e}")
            traceback.print_exc()
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_auth())
    if success:
        print("\n🎉 Debug completado - revisa los resultados arriba")
    else:
        print("\n❌ Debug falló - revisa los errores")