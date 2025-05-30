#!/usr/bin/env python3
"""
Script para limpiar datos problemáticos en la base de datos
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings

async def cleanup_database():
    """Limpia documentos problemáticos en la base de datos"""
    
    print("🧹 LIMPIANDO BASE DE DATOS...")
    print("=" * 50)
    
    try:
        # Conectar a MongoDB
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # 1. Limpiar documentos con _id: null en audit_logs
        print("🔍 Limpiando audit_logs con _id null...")
        result1 = await db.audit_logs.delete_many({"_id": None})
        print(f"   ✅ Eliminados {result1.deleted_count} documentos problemáticos de audit_logs")
        
        # 2. Limpiar documentos con _id: null en session_logs
        print("🔍 Limpiando session_logs con _id null...")
        result2 = await db.session_logs.delete_many({"_id": None})
        print(f"   ✅ Eliminados {result2.deleted_count} documentos problemáticos de session_logs")
        
        # 3. Mostrar estadísticas de colecciones
        print("\n📊 ESTADÍSTICAS DE COLECCIONES:")
        
        collections_info = [
            ("users", "Usuarios"),
            ("products", "Productos"),
            ("accounts", "Cuentas"),
            ("audit_logs", "Logs de auditoría"),
            ("session_logs", "Logs de sesión")
        ]
        
        for collection_name, description in collections_info:
            try:
                count = await db[collection_name].count_documents({})
                print(f"   📋 {description}: {count} documentos")
            except Exception as e:
                print(f"   ❌ {description}: Error contando - {e}")
        
        # 4. Verificar usuario admin
        print("\n👤 VERIFICANDO USUARIO ADMIN:")
        admin_user = await db.users.find_one({"email": "admin@supermarket.com"})
        if admin_user:
            print("   ✅ Usuario admin existe")
            print(f"   📧 Email: {admin_user.get('email')}")
            print(f"   👤 Username: {admin_user.get('username')}")
            print(f"   🔑 Role: {admin_user.get('role')}")
        else:
            print("   ❌ Usuario admin NO encontrado")
        
        await client.close()
        
        print("\n🎉 LIMPIEZA COMPLETADA!")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(cleanup_database())
    if success:
        print("\n🚀 Base de datos limpia - puedes ejecutar la aplicación")
    else:
        print("\n🔧 Revisa la configuración y vuelve a intentar")