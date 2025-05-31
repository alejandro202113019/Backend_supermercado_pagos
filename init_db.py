#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos sintéticos
"""

import asyncio
import os
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv
from bson import ObjectId

# Cargar variables de entorno
load_dotenv()

async def init_database():
    """Inicializa la base de datos y crea datos sintéticos"""
    
    try:
        # Importar después de cargar las variables de entorno
        from motor.motor_asyncio import AsyncIOMotorClient
        from utils.security import get_password_hash
        from services.encryption_service import encryption_service
        from config.settings import settings
        
        print("🔧 Inicializando base de datos con datos sintéticos...")
        print(f"📊 Base de datos: {settings.database_name}")
        
        # Conectar a MongoDB
        client = AsyncIOMotorClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Probar conexión
        await client.admin.command('ping')
        print("✅ Conexión a MongoDB exitosa!")
        
        # ========================================
        # 1. CREAR USUARIOS
        # ========================================
        print("\n👥 Creando usuarios...")
        
        users_data = [
            {
                "email": "admin@supermarket.com",
                "username": "admin",
                "full_name": "Administrador del Sistema",
                "phone": "3001234567",
                "address": "Calle 123 #45-67, Bogotá",
                "role": "admin",
                "status": "active",
                "password": "Admin123!"
            },
            {
                "email": "juan.perez@email.com",
                "username": "juan.perez",
                "full_name": "Juan Carlos Pérez",
                "phone": "3109876543",
                "address": "Carrera 15 #23-45, Bogotá",
                "role": "client",
                "status": "active",
                "password": "Cliente123!"
            },
            {
                "email": "maria.garcia@email.com",
                "username": "maria.garcia",
                "full_name": "María Fernanda García",
                "phone": "3125678901",
                "address": "Avenida 68 #12-34, Bogotá",
                "role": "client",
                "status": "active",
                "password": "Cliente123!"
            },
            {
                "email": "carlos.rodriguez@email.com",
                "username": "carlos.rodriguez",
                "full_name": "Carlos Alberto Rodríguez",
                "phone": "3134567890",
                "address": "Calle 45 #78-90, Bogotá",
                "role": "client",
                "status": "active",
                "password": "Cliente123!"
            },
            {
                "email": "ana.martinez@email.com",
                "username": "ana.martinez",
                "full_name": "Ana Lucía Martínez",
                "phone": "3143456789",
                "address": "Carrera 7 #56-78, Bogotá",
                "role": "client",
                "status": "active",
                "password": "Cliente123!"
            },
            {
                "email": "luis.lopez@email.com",
                "username": "luis.lopez",
                "full_name": "Luis Fernando López",
                "phone": "3152345678",
                "address": "Calle 100 #34-56, Bogotá",
                "role": "client",
                "status": "inactive",
                "password": "Cliente123!"
            }
        ]
        
        created_users = {}
        for user_data in users_data:
            existing_user = await db.users.find_one({"email": user_data["email"]})
            
            if not existing_user:
                user_doc = {
                    "email": user_data["email"],
                    "username": user_data["username"],
                    "full_name": user_data["full_name"],
                    "phone": user_data["phone"],
                    "address": user_data["address"],
                    "role": user_data["role"],
                    "status": user_data["status"],
                    "hashed_password": get_password_hash(user_data["password"]),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "failed_login_attempts": 0,
                    "password_changed_at": datetime.utcnow()
                }
                
                # Cifrar campos sensibles
                user_doc = encryption_service.encrypt_sensitive_fields(
                    user_doc, 
                    ["phone", "address"]
                )
                
                result = await db.users.insert_one(user_doc)
                created_users[user_data["email"]] = str(result.inserted_id)
                print(f"   ✅ Usuario creado: {user_data['full_name']}")
            else:
                created_users[user_data["email"]] = str(existing_user["_id"])
                print(f"   ℹ️  Usuario ya existe: {user_data['full_name']}")
        
        # ========================================
        # 2. CREAR PRODUCTOS
        # ========================================
        print("\n🛒 Creando productos...")
        
        products_data = [
            {
                "name": "Arroz Diana x 1kg",
                "description": "Arroz blanco premium de primera calidad",
                "price": 4500.0,
                "category": "food",
                "brand": "Diana",
                "barcode": "7702011234567",
                "stock": 150,
                "min_stock": 20
            },
            {
                "name": "Aceite Girasol x 1L",
                "description": "Aceite de girasol refinado para cocinar",
                "price": 8900.0,
                "category": "food",
                "brand": "La Favorita",
                "barcode": "7702022345678",
                "stock": 85,
                "min_stock": 15
            },
            {
                "name": "Coca Cola x 350ml",
                "description": "Bebida gaseosa sabor cola",
                "price": 2800.0,
                "category": "beverages",
                "brand": "Coca Cola",
                "barcode": "7702033456789",
                "stock": 200,
                "min_stock": 50
            },
            {
                "name": "Detergente Ariel x 1kg",
                "description": "Detergente en polvo para ropa",
                "price": 15200.0,
                "category": "cleaning",
                "brand": "Ariel",
                "barcode": "7702044567890",
                "stock": 45,
                "min_stock": 10
            },
            {
                "name": "Shampoo Head & Shoulders",
                "description": "Shampoo anticaspa 400ml",
                "price": 18500.0,
                "category": "personal_care",
                "brand": "Head & Shoulders",
                "barcode": "7702055678901",
                "stock": 35,
                "min_stock": 8
            },
            {
                "name": "Papel Higiénico Familia x 4",
                "description": "Papel higiénico suave doble hoja",
                "price": 12800.0,
                "category": "home",
                "brand": "Familia",
                "barcode": "7702066789012",
                "stock": 120,
                "min_stock": 25
            }
        ]
        
        created_products = []
        for product_data in products_data:
            existing_product = await db.products.find_one({"barcode": product_data["barcode"]})
            
            if not existing_product:
                product_doc = {
                    **product_data,
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "created_by": created_users["admin@supermarket.com"]
                }
                
                result = await db.products.insert_one(product_doc)
                created_products.append({
                    "id": str(result.inserted_id),
                    "name": product_data["name"],
                    "price": product_data["price"]
                })
                print(f"   ✅ Producto creado: {product_data['name']}")
            else:
                created_products.append({
                    "id": str(existing_product["_id"]),
                    "name": existing_product["name"],
                    "price": existing_product["price"]
                })
                print(f"   ℹ️  Producto ya existe: {product_data['name']}")
        
        # ========================================
        # 3. CREAR CUENTAS
        # ========================================
        print("\n🧾 Creando cuentas...")
        
        # Obtener algunos clientes para las cuentas
        clients = [
            {"id": created_users["juan.perez@email.com"], "name": "Juan Carlos Pérez", "email": "juan.perez@email.com"},
            {"id": created_users["maria.garcia@email.com"], "name": "María Fernanda García", "email": "maria.garcia@email.com"},
            {"id": created_users["carlos.rodriguez@email.com"], "name": "Carlos Alberto Rodríguez", "email": "carlos.rodriguez@email.com"},
            {"id": created_users["ana.martinez@email.com"], "name": "Ana Lucía Martínez", "email": "ana.martinez@email.com"}
        ]
        
        accounts_data = [
            {
                "client": clients[0],
                "items": [
                    {"product_idx": 0, "quantity": 2},  # Arroz x 2
                    {"product_idx": 1, "quantity": 1},  # Aceite x 1
                    {"product_idx": 2, "quantity": 6}   # Coca Cola x 6
                ],
                "status": "pending",
                "due_date": datetime.utcnow() + timedelta(days=15),
                "discount": 0.0,
                "tax": 0.0
            },
            {
                "client": clients[1],
                "items": [
                    {"product_idx": 3, "quantity": 1},  # Detergente x 1
                    {"product_idx": 4, "quantity": 1},  # Shampoo x 1
                    {"product_idx": 5, "quantity": 2}   # Papel higiénico x 2
                ],
                "status": "paid",
                "due_date": datetime.utcnow() + timedelta(days=10),
                "discount": 5.0,  # 5% descuento
                "tax": 19.0       # 19% IVA
            },
            {
                "client": clients[2],
                "items": [
                    {"product_idx": 0, "quantity": 3},  # Arroz x 3
                    {"product_idx": 2, "quantity": 12}  # Coca Cola x 12
                ],
                "status": "overdue",
                "due_date": datetime.utcnow() - timedelta(days=5),
                "discount": 0.0,
                "tax": 0.0
            },
            {
                "client": clients[3],
                "items": [
                    {"product_idx": 1, "quantity": 2},  # Aceite x 2
                    {"product_idx": 3, "quantity": 1},  # Detergente x 1
                    {"product_idx": 5, "quantity": 3}   # Papel higiénico x 3
                ],
                "status": "pending",
                "due_date": datetime.utcnow() + timedelta(days=20),
                "discount": 10.0,  # 10% descuento
                "tax": 19.0        # 19% IVA
            },
            {
                "client": clients[0],
                "items": [
                    {"product_idx": 4, "quantity": 2},  # Shampoo x 2
                    {"product_idx": 2, "quantity": 4}   # Coca Cola x 4
                ],
                "status": "cancelled",
                "due_date": datetime.utcnow() + timedelta(days=7),
                "discount": 0.0,
                "tax": 0.0
            }
        ]
        
        created_accounts = []
        for i, account_data in enumerate(accounts_data):
            # Calcular items y totales
            items = []
            subtotal = 0.0
            
            for item in account_data["items"]:
                product = created_products[item["product_idx"]]
                total_price = product["price"] * item["quantity"]
                subtotal += total_price
                
                items.append({
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": item["quantity"],
                    "unit_price": product["price"],
                    "total_price": total_price
                })
            
            # Calcular totales
            discount_amount = subtotal * (account_data["discount"] / 100) if account_data["discount"] > 0 else 0.0
            tax_amount = subtotal * (account_data["tax"] / 100) if account_data["tax"] > 0 else 0.0
            total_amount = subtotal - discount_amount + tax_amount
            
            # Generar número de cuenta
            account_number = f"ACC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            account_doc = {
                "account_number": account_number,
                "client_id": account_data["client"]["id"],
                "client_name": account_data["client"]["name"],
                "client_email": account_data["client"]["email"],
                "items": items,
                "subtotal": subtotal,
                "tax": tax_amount,
                "discount": discount_amount,
                "total_amount": total_amount,
                "status": account_data["status"],
                "due_date": account_data["due_date"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": created_users["admin@supermarket.com"],
                "payments": [],
                "notes": f"Cuenta de prueba #{i+1}"
            }
            
            # Si la cuenta está pagada, agregar un pago
            if account_data["status"] == "paid":
                payment = {
                    "payment_date": datetime.utcnow() - timedelta(days=2),
                    "amount": total_amount,
                    "payment_method": "card",
                    "reference": f"TXN{str(uuid.uuid4())[:8].upper()}",
                    "processed_by": created_users["admin@supermarket.com"]
                }
                account_doc["payments"] = [payment]
            
            result = await db.accounts.insert_one(account_doc)
            created_accounts.append(str(result.inserted_id))
            print(f"   ✅ Cuenta creada: {account_number} - {account_data['client']['name']}")
        
        # ========================================
        # 4. CREAR LOGS DE AUDITORÍA
        # ========================================
        print("\n📝 Creando logs de auditoría...")
        
        audit_logs = [
            {
                "user_id": created_users["admin@supermarket.com"],
                "username": "admin",
                "action": "login",
                "resource": "auth",
                "details": {"method": "email_password"},
                "ip_address": "192.168.1.100",
                "user_agent": "PostmanRuntime/7.28.4",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "level": "info",
                "success": True
            },
            {
                "user_id": created_users["admin@supermarket.com"],
                "username": "admin",
                "action": "create",
                "resource": "product",
                "resource_id": created_products[0]["id"],
                "details": {"product_name": created_products[0]["name"]},
                "ip_address": "192.168.1.100",
                "timestamp": datetime.utcnow() - timedelta(hours=1, minutes=30),
                "level": "info",
                "success": True
            },
            {
                "user_id": created_users["juan.perez@email.com"],
                "username": "juan.perez",
                "action": "login",
                "resource": "auth",
                "details": {"method": "email_password"},
                "ip_address": "192.168.1.101",
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "level": "info",
                "success": True
            },
            {
                "user_id": created_users["admin@supermarket.com"],
                "username": "admin",
                "action": "create",
                "resource": "account",
                "resource_id": created_accounts[0],
                "details": {"client_name": clients[0]["name"], "total_amount": 26400.0},
                "ip_address": "192.168.1.100",
                "timestamp": datetime.utcnow() - timedelta(minutes=30),
                "level": "info",
                "success": True
            },
            {
                "user_id": created_users["maria.garcia@email.com"],
                "username": "maria.garcia",
                "action": "payment",
                "resource": "account",
                "resource_id": created_accounts[1],
                "details": {"payment_method": "card", "amount": 55404.0},
                "ip_address": "192.168.1.102",
                "timestamp": datetime.utcnow() - timedelta(minutes=15),
                "level": "info",
                "success": True
            }
        ]
        
        for audit_log in audit_logs:
            await db.audit_logs.insert_one(audit_log)
        
        print(f"   ✅ {len(audit_logs)} logs de auditoría creados")
        
        # ========================================
        # 5. CREAR LOGS DE SESIÓN
        # ========================================
        print("\n🔐 Creando logs de sesión...")
        
        session_logs = [
            {
                "user_id": created_users["admin@supermarket.com"],
                "username": "admin",
                "session_id": str(uuid.uuid4()),
                "login_time": datetime.utcnow() - timedelta(hours=2),
                "logout_time": datetime.utcnow() - timedelta(hours=1),
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "is_active": False,
                "last_activity": datetime.utcnow() - timedelta(hours=1)
            },
            {
                "user_id": created_users["juan.perez@email.com"],
                "username": "juan.perez",
                "session_id": str(uuid.uuid4()),
                "login_time": datetime.utcnow() - timedelta(hours=1),
                "ip_address": "192.168.1.101",
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
                "is_active": True,
                "last_activity": datetime.utcnow() - timedelta(minutes=10)
            },
            {
                "user_id": created_users["maria.garcia@email.com"],
                "username": "maria.garcia",
                "session_id": str(uuid.uuid4()),
                "login_time": datetime.utcnow() - timedelta(minutes=45),
                "ip_address": "192.168.1.102",
                "user_agent": "PostmanRuntime/7.28.4",
                "is_active": True,
                "last_activity": datetime.utcnow() - timedelta(minutes=5)
            }
        ]
        
        for session_log in session_logs:
            await db.session_logs.insert_one(session_log)
        
        print(f"   ✅ {len(session_logs)} logs de sesión creados")
        
        # ========================================
        # MOSTRAR ESTADÍSTICAS
        # ========================================
        print("\n📊 ESTADÍSTICAS FINALES:")
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
                print(f"   ❌ {description}: Error - {e}")
        
        client.close()
        print("\n🎉 Inicialización completada con datos sintéticos!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Detalles del error:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(init_database())
    if success:
        print("\n✅ Base de datos lista con datos sintéticos!")
        print("🚀 Para iniciar el servidor ejecuta: python app.py")
        
        print("\n🔐 CREDENCIALES PARA PROBAR:")
        print("=" * 50)
        print("👨‍💼 ADMIN:")
        print("   📧 Email: admin@supermarket.com")
        print("   🔑 Password: Admin123!")
        
        print("\n👥 CLIENTES:")
        print("   📧 Email: juan.perez@email.com")
        print("   🔑 Password: Cliente123!")
        print("   📧 Email: maria.garcia@email.com")
        print("   🔑 Password: Cliente123!")
        print("   📧 Email: carlos.rodriguez@email.com")
        print("   🔑 Password: Cliente123!")
        print("   📧 Email: ana.martinez@email.com")
        print("   🔑 Password: Cliente123!")
        
        print("\n🛒 DATOS CREADOS:")
        print("   - 6 usuarios (1 admin + 5 clientes)")
        print("   - 6 productos de diferentes categorías")
        print("   - 5 cuentas con diferentes estados")
        print("   - 5 logs de auditoría")
        print("   - 3 logs de sesión")
        
        print("\n📚 ENDPOINTS PARA PROBAR EN POSTMAN:")
        print("   POST /auth/login - Autenticación")
        print("   GET /auth/me - Información del usuario")
        print("   GET /users - Lista de usuarios (admin)")
        print("   GET /products - Lista de productos")
        print("   GET /accounts - Lista de cuentas")
        print("   POST /accounts/{id}/payment - Procesar pago")
        
    else:
        print("\n❌ Error en la inicialización")
        print("🔧 Revisa tu archivo .env y la conexión a MongoDB")