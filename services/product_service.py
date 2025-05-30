from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from models.product import Product, ProductStatus, ProductCategory
from schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductSearchFilters
from utils.validators import validate_positive_number
from utils.exceptions import ValidationException, NotFoundException


class ProductService:
    def __init__(self):
        self.collection = "products"
    
    async def get_database(self):
        """Obtiene la base de datos - importación diferida para evitar circular imports"""
        from config.database import get_database
        return await get_database()
    
    async def get_audit_service(self):
        """Obtiene el servicio de auditoría - importación diferida"""
        from services.audit_service import audit_service
        return audit_service
    
    async def create_product(
        self,
        product_data: ProductCreate,
        created_by_id: str,
        ip_address: str
    ) -> Product:
        """Crea un nuevo producto"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        # Validaciones
        validate_positive_number(product_data.price, "price")
        
        # Verificar si el código de barras ya existe (si se proporciona)
        if product_data.barcode:
            existing_barcode = await db[self.collection].find_one({
                "barcode": product_data.barcode,
                "status": {"$ne": ProductStatus.DISCONTINUED}
            })
            if existing_barcode:
                raise ValidationException("El código de barras ya está en uso")
        
        # Crear producto
        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            category=product_data.category,
            brand=product_data.brand,
            barcode=product_data.barcode,
            stock=product_data.stock,
            min_stock=product_data.min_stock,
            created_by=created_by_id
        )
        
        # Insertar en base de datos
        product_doc = product.dict(by_alias=True, exclude={"id"})
        result = await db[self.collection].insert_one(product_doc)
        product.id = str(result.inserted_id)
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=created_by_id,
            username="admin",
            action="create",
            resource="product",
            resource_id=str(product.id),
            details={
                "name": product.name,
                "price": product.price,
                "category": product.category,
                "created_by": created_by_id
            },
            ip_address=ip_address
        )
        
        return product
    
    async def get_product_by_id(self, product_id: str) -> Product:
        """Obtiene un producto por ID"""
        db: AsyncIOMotorDatabase = await self.get_database()
        
        if not ObjectId.is_valid(product_id):
            raise ValidationException("ID de producto inválido")
        
        product_doc = await db[self.collection].find_one({"_id": ObjectId(product_id)})
        if not product_doc:
            raise NotFoundException("Producto no encontrado")
        
        return Product(**product_doc)
    
    async def update_product(
        self,
        product_id: str,
        product_data: ProductUpdate,
        updated_by_id: str,
        ip_address: str
    ) -> Product:
        """Actualiza un producto"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        if not ObjectId.is_valid(product_id):
            raise ValidationException("ID de producto inválido")
        
        # Verificar que el producto existe
        existing_product = await db[self.collection].find_one({"_id": ObjectId(product_id)})
        if not existing_product:
            raise NotFoundException("Producto no encontrado")
        
        # Preparar datos de actualización
        update_data = {}
        original_data = {}
        
        if product_data.name is not None:
            update_data["name"] = product_data.name
            original_data["name"] = existing_product.get("name")
        
        if product_data.description is not None:
            update_data["description"] = product_data.description
            original_data["description"] = existing_product.get("description")
        
        if product_data.price is not None:
            validate_positive_number(product_data.price, "price")
            update_data["price"] = product_data.price
            original_data["price"] = existing_product.get("price")
        
        if product_data.category is not None:
            update_data["category"] = product_data.category
            original_data["category"] = existing_product.get("category")
        
        if product_data.brand is not None:
            update_data["brand"] = product_data.brand
            original_data["brand"] = existing_product.get("brand")
        
        if product_data.barcode is not None:
            # Verificar que el código de barras no esté en uso por otro producto
            existing_barcode = await db[self.collection].find_one({
                "barcode": product_data.barcode,
                "_id": {"$ne": ObjectId(product_id)},
                "status": {"$ne": ProductStatus.DISCONTINUED}
            })
            if existing_barcode:
                raise ValidationException("El código de barras ya está en uso")
            update_data["barcode"] = product_data.barcode
            original_data["barcode"] = existing_product.get("barcode")
        
        if product_data.stock is not None:
            update_data["stock"] = product_data.stock
            original_data["stock"] = existing_product.get("stock")
        
        if product_data.min_stock is not None:
            update_data["min_stock"] = product_data.min_stock
            original_data["min_stock"] = existing_product.get("min_stock")
        
        if product_data.status is not None:
            update_data["status"] = product_data.status
            original_data["status"] = existing_product.get("status")
        
        if not update_data:
            raise ValidationException("No hay datos para actualizar")
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Actualizar en base de datos
        await db[self.collection].update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=updated_by_id,
            username="admin",
            action="update",
            resource="product",
            resource_id=product_id,
            details={
                "updated_fields": list(update_data.keys()),
                "original_data": original_data,
                "updated_by": updated_by_id
            },
            ip_address=ip_address
        )
        
        # Obtener producto actualizado
        return await self.get_product_by_id(product_id)
    
    async def delete_product(
        self,
        product_id: str,
        deleted_by_id: str,
        ip_address: str
    ) -> bool:
        """Elimina un producto (soft delete)"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        if not ObjectId.is_valid(product_id):
            raise ValidationException("ID de producto inválido")
        
        # Verificar que el producto existe
        existing_product = await db[self.collection].find_one({"_id": ObjectId(product_id)})
        if not existing_product:
            raise NotFoundException("Producto no encontrado")
        
        # Soft delete - cambiar estado a discontinuado
        await db[self.collection].update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "status": ProductStatus.DISCONTINUED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=deleted_by_id,
            username="admin",
            action="delete",
            resource="product",
            resource_id=product_id,
            details={
                "name": existing_product.get("name"),
                "deleted_by": deleted_by_id
            },
            ip_address=ip_address
        )
        
        return True
    
    async def get_products(
        self,
        page: int = 1,
        size: int = 50,
        filters: Optional[ProductSearchFilters] = None
    ) -> Dict[str, Any]:
        """Obtiene lista de productos con paginación y filtros"""
        db: AsyncIOMotorDatabase = await self.get_database()
        
        # Construir query
        query = {}
        
        if filters:
            if filters.name:
                query["name"] = {"$regex": filters.name, "$options": "i"}
            
            if filters.category:
                query["category"] = filters.category
            
            if filters.brand:
                query["brand"] = {"$regex": filters.brand, "$options": "i"}
            
            if filters.status:
                query["status"] = filters.status
            
            if filters.min_price is not None or filters.max_price is not None:
                price_query = {}
                if filters.min_price is not None:
                    price_query["$gte"] = filters.min_price
                if filters.max_price is not None:
                    price_query["$lte"] = filters.max_price
                query["price"] = price_query
        
        # Contar total
        total = await db[self.collection].count_documents(query)
        
        # Obtener productos paginados
        skip = (page - 1) * size
        cursor = db[self.collection].find(query).sort("created_at", -1).skip(skip).limit(size)
        products_docs = await cursor.to_list(length=size)
        
        # Convertir a response
        products = []
        for product_doc in products_docs:
            product = Product(**product_doc)
            products.append(ProductResponse(
                id=str(product.id),
                name=product.name,
                description=product.description,
                price=product.price,
                category=product.category,
                brand=product.brand,
                barcode=product.barcode,
                stock=product.stock,
                min_stock=product.min_stock,
                status=product.status,
                created_at=product.created_at,
                updated_at=product.updated_at
            ))
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "size": size
        }
    
    async def get_active_products(self) -> List[ProductResponse]:
        """Obtiene todos los productos activos"""
        db: AsyncIOMotorDatabase = await self.get_database()
        
        cursor = db[self.collection].find(
            {"status": ProductStatus.ACTIVE}
        ).sort("name", 1)
        
        products_docs = await cursor.to_list(length=None)
        
        products = []
        for product_doc in products_docs:
            product = Product(**product_doc)
            products.append(ProductResponse(
                id=str(product.id),
                name=product.name,
                description=product.description,
                price=product.price,
                category=product.category,
                brand=product.brand,
                barcode=product.barcode,
                stock=product.stock,
                min_stock=product.min_stock,
                status=product.status,
                created_at=product.created_at,
                updated_at=product.updated_at
            ))
        
        return products
    
    async def update_stock(
        self,
        product_id: str,
        quantity_change: int,
        updated_by_id: str,
        ip_address: str,
        operation: str = "manual"
    ) -> Product:
        """Actualiza el stock de un producto"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        if not ObjectId.is_valid(product_id):
            raise ValidationException("ID de producto inválido")
        
        # Obtener producto actual
        product_doc = await db[self.collection].find_one({"_id": ObjectId(product_id)})
        if not product_doc:
            raise NotFoundException("Producto no encontrado")
        
        product = Product(**product_doc)
        new_stock = product.stock + quantity_change
        
        # Validar que el stock no sea negativo
        if new_stock < 0:
            raise ValidationException("El stock no puede ser negativo")
        
        # Actualizar stock
        await db[self.collection].update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "stock": new_stock,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=updated_by_id,
            username="system",
            action="update",
            resource="product_stock",
            resource_id=product_id,
            details={
                "product_name": product.name,
                "previous_stock": product.stock,
                "quantity_change": quantity_change,
                "new_stock": new_stock,
                "operation": operation,
                "updated_by": updated_by_id
            },
            ip_address=ip_address
        )
        
        # Obtener producto actualizado
        return await self.get_product_by_id(product_id)


# Instancia global del servicio de productos
product_service = ProductService()