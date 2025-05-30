#!/usr/bin/env python3
"""
Script para probar la conexión a MongoDB Atlas
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def test_mongodb_connection():
    """Prueba la conexión a MongoDB con diferentes URLs"""
    
    print("🔧 PROBANDO CONEXIÓN A MONGODB ATLAS")
    print("=" * 50)
    
    # URL desde variables de entorno
    mongodb_url = os.getenv('MONGODB_URL')
    database_name = os.getenv('DATABASE_NAME', 'supermarket_payments')
    
    print(f"📊 Base de datos objetivo: {database_name}")
    print(f"🔗 URL desde .env: {mongodb_url[:50]}...")
    
    # Probar diferentes formatos de URL
    urls_to_test = [
        # URL original desde .env
        mongodb_url,
        
        # URL con el nombre de base de datos incluido
        f"mongodb+srv://alejandromesa:LACDU0VuYHjUESyb@cluster0.ezgsrmk.mongodb.net/{database_name}?retryWrites=true&w=majority",
        
        # URL básica sin parámetros adicionales
        "mongodb+srv://alejandromesa:LACDU0VuYHjUESyb@cluster0.ezgsrmk.mongodb.net/?retryWrites=true&w=majority",
        
        # URL con appName específico
        "mongodb+srv://alejandromesa:LACDU0VuYHjUESyb@cluster0.ezgsrmk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    ]
    
    for i, url in enumerate(urls_to_test, 1):
        if not url:
            continue
            
        print(f"\n🔄 Prueba {i}:")
        print(f"   URL: {url[:70]}...")
        
        try:
            # Crear cliente con timeout
            client = AsyncIOMotorClient(
                url,
                serverSelectionTimeoutMS=5000,  # 5 segundos de timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Probar ping
            await client.admin.command('ping')
            print(f"   ✅ ¡Conexión exitosa!")
            
            # Probar acceso a la base de datos
            db = client[database_name]
            collections = await db.list_collection_names()
            print(f"   📚 Colecciones en DB: {collections if collections else 'ninguna (DB nueva)'}")
            
            # Probar operación de escritura simple
            test_collection = db.test_connection
            result = await test_collection.insert_one({"test": True, "timestamp": "2024-01-01"})
            print(f"   ✅ Escritura exitosa: {result.inserted_id}")
            
            # Limpiar test
            await test_collection.delete_one({"_id": result.inserted_id})
            print(f"   🧹 Test limpiado")
            
            await client.close()
            
            # Si llegamos aquí, esta URL funciona
            print(f"\n🎉 ¡CONEXIÓN EXITOSA CON URL {i}!")
            print("=" * 50)
            print("✅ Usa esta URL en tu archivo .env:")
            print(f"MONGODB_URL={url}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            if "DNS" in str(e):
                print("   💡 Posible problema de DNS o conectividad de red")
            elif "auth" in str(e).lower():
                print("   💡 Problema de autenticación - verifica usuario/contraseña")
            elif "timeout" in str(e).lower():
                print("   💡 Problema de timeout - verifica acceso de red")
            
            try:
                await client.close()
            except:
                pass
    
    print("\n❌ Ninguna URL funcionó")
    print("\n🔧 PASOS PARA SOLUCIONAR:")
    print("1. Verifica que tu cluster esté activo en MongoDB Atlas")
    print("2. Verifica que tu IP esté en Network Access")
    print("3. Verifica usuario/contraseña en Database Access")
    print("4. Intenta descargar MongoDB Compass y conectarte")
    print("5. Verifica tu conexión a internet")
    
    return False

if __name__ == "__main__":
    success = asyncio.run(test_mongodb_connection())
    if success:
        print("\n🚀 ¡Listo para ejecutar la aplicación!")
    else:
        print("\n🔧 Revisa la configuración antes de continuar")