import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from models.account import Account, AccountStatus, PaymentMethod, AccountItem, PaymentRecord
from models.user import User
from models.product import Product
from schemas.account import AccountCreate, AccountUpdate, PaymentRequest, AccountResponse, AccountSearchFilters
from utils.validators import validate_positive_number
from utils.exceptions import ValidationException, NotFoundException


class AccountService:
    def __init__(self):
        self.collection = "accounts"
    
    async def get_database(self):
        """Obtiene la base de datos - importación diferida para evitar circular imports"""
        from config.database import get_database
        return await get_database()
    
    async def get_audit_service(self):
        """Obtiene el servicio de auditoría - importación diferida"""
        from services.audit_service import audit_service
        return audit_service
    
    async def get_user_service(self):
        """Obtiene el servicio de usuarios - importación diferida"""
        from services.user_service import user_service
        return user_service
    
    async def get_product_service(self):
        """Obtiene el servicio de productos - importación diferida"""
        from services.product_service import product_service
        return product_service
    
    def _generate_account_number(self) -> str:
        """Genera un número único de cuenta"""
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"ACC-{timestamp}-{unique_id}"
    
    async def create_account(
        self,
        account_data: AccountCreate,
        created_by_id: str,
        ip_address: str
    ) -> Account:
        """Crea una nueva cuenta pendiente"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        user_service = await self.get_user_service()
        product_service = await self.get_product_service()
        
        # Validar que el cliente existe
        client = await user_service.get_user_by_id(account_data.client_id)
        
        # Validar y procesar items
        items = []
        subtotal = 0.0
        
        for item_data in account_data.items:
            # Obtener producto
            product = await product_service.get_product_by_id(item_data.product_id)
            
            # Validar cantidad
            validate_positive_number(item_data.quantity, "quantity")
            
            # Calcular precio total del item
            total_price = product.price * item_data.quantity
            subtotal += total_price
            
            # Crear item de cuenta
            account_item = AccountItem(
                product_id=str(product.id),
                product_name=product.name,
                quantity=item_data.quantity,
                unit_price=product.price,
                total_price=total_price
            )
            items.append(account_item)
        
        # Calcular totales
        tax_amount = subtotal * (account_data.tax / 100) if account_data.tax > 0 else 0.0
        discount_amount = subtotal * (account_data.discount / 100) if account_data.discount > 0 else 0.0
        total_amount = subtotal + tax_amount - discount_amount
        
        # Crear cuenta
        account = Account(
            account_number=self._generate_account_number(),
            client_id=str(client.id),
            client_name=client.full_name,
            client_email=client.email,
            items=items,
            subtotal=subtotal,
            tax=tax_amount,
            discount=discount_amount,
            total_amount=total_amount,
            due_date=account_data.due_date,
            created_by=created_by_id,
            notes=account_data.notes
        )
        
        # Insertar en base de datos
        account_doc = account.dict(by_alias=True, exclude={"id"})
        result = await db[self.collection].insert_one(account_doc)
        account.id = str(result.inserted_id)
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=created_by_id,
            username="admin",
            action="create",
            resource="account",
            resource_id=str(account.id),
            details={
                "account_number": account.account_number,
                "client_id": account.client_id,
                "client_name": account.client_name,
                "total_amount": account.total_amount,
                "items_count": len(items),
                "created_by": created_by_id
            },
            ip_address=ip_address
        )
        
        return account
    
    async def get_account_by_id(self, account_id: str) -> Account:
        """Obtiene una cuenta por ID"""
        db: AsyncIOMotorDatabase = await self.get_database()
        
        if not ObjectId.is_valid(account_id):
            raise ValidationException("ID de cuenta inválido")
        
        account_doc = await db[self.collection].find_one({"_id": ObjectId(account_id)})
        if not account_doc:
            raise NotFoundException("Cuenta no encontrada")
        
        return Account(**account_doc)
    
    async def update_account(
        self,
        account_id: str,
        account_data: AccountUpdate,
        updated_by_id: str,
        ip_address: str
    ) -> Account:
        """Actualiza una cuenta"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        product_service = await self.get_product_service()
        
        if not ObjectId.is_valid(account_id):
            raise ValidationException("ID de cuenta inválido")
        
        # Verificar que la cuenta existe
        existing_account = await db[self.collection].find_one({"_id": ObjectId(account_id)})
        if not existing_account:
            raise NotFoundException("Cuenta no encontrada")
        
        account = Account(**existing_account)
        
        # Solo permitir actualización si la cuenta está pendiente
        if account.status != AccountStatus.PENDING:
            raise ValidationException("Solo se pueden actualizar cuentas pendientes")
        
        # Preparar datos de actualización
        update_data = {}
        original_data = {}
        
        # Actualizar items si se proporcionan
        if account_data.items is not None:
            items = []
            subtotal = 0.0
            
            for item_data in account_data.items:
                # Obtener producto
                product = await product_service.get_product_by_id(item_data.product_id)
                
                # Validar cantidad
                validate_positive_number(item_data.quantity, "quantity")
                
                # Calcular precio total del item
                total_price = product.price * item_data.quantity
                subtotal += total_price
                
                # Crear item de cuenta
                account_item = AccountItem(
                    product_id=str(product.id),
                    product_name=product.name,
                    quantity=item_data.quantity,
                    unit_price=product.price,
                    total_price=total_price
                )
                items.append(account_item)
            
            # Recalcular totales
            tax_rate = account_data.tax if account_data.tax is not None else (account.tax / account.subtotal * 100 if account.subtotal > 0 else 0)
            discount_rate = account_data.discount if account_data.discount is not None else (account.discount / account.subtotal * 100 if account.subtotal > 0 else 0)
            
            tax_amount = subtotal * (tax_rate / 100) if tax_rate > 0 else 0.0
            discount_amount = subtotal * (discount_rate / 100) if discount_rate > 0 else 0.0
            total_amount = subtotal + tax_amount - discount_amount
            
            update_data.update({
                "items": [item.dict() for item in items],
                "subtotal": subtotal,
                "tax": tax_amount,
                "discount": discount_amount,
                "total_amount": total_amount
            })
            original_data["items_count"] = len(account.items)
            original_data["subtotal"] = account.subtotal
            original_data["total_amount"] = account.total_amount
        
        if account_data.due_date is not None:
            update_data["due_date"] = account_data.due_date
            original_data["due_date"] = account.due_date
        
        if account_data.status is not None:
            update_data["status"] = account_data.status
            original_data["status"] = account.status
        
        if account_data.notes is not None:
            update_data["notes"] = account_data.notes
            original_data["notes"] = account.notes
        
        if not update_data:
            raise ValidationException("No hay datos para actualizar")
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Actualizar en base de datos
        await db[self.collection].update_one(
            {"_id": ObjectId(account_id)},
            {"$set": update_data}
        )
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=updated_by_id,
            username="admin",
            action="update",
            resource="account",
            resource_id=account_id,
            details={
                "account_number": account.account_number,
                "updated_fields": list(update_data.keys()),
                "original_data": original_data,
                "updated_by": updated_by_id
            },
            ip_address=ip_address
        )
        
        # Obtener cuenta actualizada
        return await self.get_account_by_id(account_id)
    
    async def process_payment(
        self,
        account_id: str,
        payment_data: PaymentRequest,
        processed_by_id: str,
        ip_address: str
    ) -> Account:
        """Procesa un pago para una cuenta"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        if not ObjectId.is_valid(account_id):
            raise ValidationException("ID de cuenta inválido")
        
        # Obtener cuenta
        account = await self.get_account_by_id(account_id)
        
        # Validar que la cuenta esté pendiente
        if account.status != AccountStatus.PENDING:
            raise ValidationException("Solo se pueden pagar cuentas pendientes")
        
        # Validar monto
        validate_positive_number(payment_data.amount, "amount")
        
        # Calcular total pagado hasta ahora
        total_paid = sum(payment.amount for payment in account.payments)
        remaining_amount = account.total_amount - total_paid
        
        if payment_data.amount > remaining_amount:
            raise ValidationException(f"El monto excede el saldo pendiente de ${remaining_amount:.2f}")
        
        # Crear registro de pago
        payment_record = PaymentRecord(
            payment_date=datetime.utcnow(),
            amount=payment_data.amount,
            payment_method=payment_data.payment_method,
            reference=payment_data.reference,
            processed_by=processed_by_id
        )
        
        # Calcular nuevo total pagado
        new_total_paid = total_paid + payment_data.amount
        new_status = AccountStatus.PAID if new_total_paid >= account.total_amount else AccountStatus.PENDING
        
        # Actualizar cuenta
        await db[self.collection].update_one(
            {"_id": ObjectId(account_id)},
            {
                "$push": {"payments": payment_record.dict()},
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=processed_by_id,
            username="user",
            action="payment",
            resource="account",
            resource_id=account_id,
            details={
                "account_number": account.account_number,
                "client_name": account.client_name,
                "payment_amount": payment_data.amount,
                "payment_method": payment_data.payment_method,
                "reference": payment_data.reference,
                "total_paid": new_total_paid,
                "remaining_amount": account.total_amount - new_total_paid,
                "new_status": new_status,
                "processed_by": processed_by_id
            },
            ip_address=ip_address
        )
        
        # Obtener cuenta actualizada
        return await self.get_account_by_id(account_id)
    
    async def get_accounts(
        self,
        page: int = 1,
        size: int = 50,
        filters: Optional[AccountSearchFilters] = None,
        client_id: Optional[str] = None  # Para filtrar por cliente específico
    ) -> Dict[str, Any]:
        """Obtiene lista de cuentas con paginación y filtros"""
        db: AsyncIOMotorDatabase = await self.get_database()
        
        # Construir query
        query = {}
        
        # Si se especifica client_id, filtrar por ese cliente
        if client_id:
            query["client_id"] = client_id
        
        if filters:
            if filters.client_id:
                query["client_id"] = filters.client_id
            
            if filters.status:
                query["status"] = filters.status
            
            if filters.due_date_from or filters.due_date_to:
                date_query = {}
                if filters.due_date_from:
                    date_query["$gte"] = filters.due_date_from
                if filters.due_date_to:
                    date_query["$lte"] = filters.due_date_to
                query["due_date"] = date_query
            
            if filters.min_amount is not None or filters.max_amount is not None:
                amount_query = {}
                if filters.min_amount is not None:
                    amount_query["$gte"] = filters.min_amount
                if filters.max_amount is not None:
                    amount_query["$lte"] = filters.max_amount
                query["total_amount"] = amount_query
        
        # Contar total
        total = await db[self.collection].count_documents(query)
        
        # Obtener cuentas paginadas
        skip = (page - 1) * size
        cursor = db[self.collection].find(query).sort("created_at", -1).skip(skip).limit(size)
        accounts_docs = await cursor.to_list(length=size)
        
        # Convertir a response
        accounts = []
        for account_doc in accounts_docs:
            account = Account(**account_doc)
            accounts.append(AccountResponse(
                id=str(account.id),
                account_number=account.account_number,
                client_id=account.client_id,
                client_name=account.client_name,
                client_email=account.client_email,
                items=account.items,
                subtotal=account.subtotal,
                tax=account.tax,
                discount=account.discount,
                total_amount=account.total_amount,
                status=account.status,
                due_date=account.due_date,
                created_at=account.created_at,
                updated_at=account.updated_at,
                payments=account.payments,
                notes=account.notes
            ))
        
        return {
            "accounts": accounts,
            "total": total,
            "page": page,
            "size": size
        }
    
    async def get_client_accounts(
        self,
        client_id: str,
        page: int = 1,
        size: int = 50,
        status: Optional[AccountStatus] = None
    ) -> Dict[str, Any]:
        """Obtiene las cuentas de un cliente específico"""
        user_service = await self.get_user_service()
        
        # Validar que el cliente existe
        await user_service.get_user_by_id(client_id)
        
        # Crear filtros
        from schemas.account import AccountSearchFilters
        filters = AccountSearchFilters(client_id=client_id, status=status)
        
        return await self.get_accounts(page, size, filters, client_id)
    
    async def delete_account(
        self,
        account_id: str,
        deleted_by_id: str,
        ip_address: str
    ) -> bool:
        """Elimina una cuenta (solo si está pendiente y sin pagos)"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        if not ObjectId.is_valid(account_id):
            raise ValidationException("ID de cuenta inválido")
        
        # Verificar que la cuenta existe
        account = await self.get_account_by_id(account_id)
        
        # Solo permitir eliminación si está pendiente y sin pagos
        if account.status != AccountStatus.PENDING:
            raise ValidationException("Solo se pueden eliminar cuentas pendientes")
        
        if account.payments:
            raise ValidationException("No se pueden eliminar cuentas con pagos registrados")
        
        # Cambiar estado a cancelado en lugar de eliminar
        await db[self.collection].update_one(
            {"_id": ObjectId(account_id)},
            {
                "$set": {
                    "status": AccountStatus.CANCELLED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=deleted_by_id,
            username="admin",
            action="delete",
            resource="account",
            resource_id=account_id,
            details={
                "account_number": account.account_number,
                "client_name": account.client_name,
                "total_amount": account.total_amount,
                "deleted_by": deleted_by_id
            },
            ip_address=ip_address
        )
        
        return True
    
    async def get_payment_summary(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene resumen de pagos"""
        db: AsyncIOMotorDatabase = await self.get_database()
        
        # Pipeline de agregación
        pipeline = []
        
        # Filtrar por cliente si se especifica
        if client_id:
            pipeline.append({"$match": {"client_id": client_id}})
        
        # Agregar campos calculados
        pipeline.extend([
            {
                "$addFields": {
                    "total_paid_per_account": {"$sum": "$payments.amount"},
                    "remaining_amount": {
                        "$subtract": ["$total_amount", {"$sum": "$payments.amount"}]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_accounts": {"$sum": 1},
                    "total_pending_amount": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", "pending"]},
                                "$remaining_amount",
                                0
                            ]
                        }
                    },
                    "total_paid_amount": {"$sum": "$total_paid_per_account"},
                    "pending_accounts": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", "pending"]}, 1, 0]
                        }
                    },
                    "paid_accounts": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", "paid"]}, 1, 0]
                        }
                    },
                    "overdue_accounts": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", "overdue"]}, 1, 0]
                        }
                    }
                }
            }
        ])
        
        result = await db[self.collection].aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "total_accounts": 0,
                "total_pending_amount": 0.0,
                "total_paid_amount": 0.0,
                "pending_accounts": 0,
                "paid_accounts": 0,
                "overdue_accounts": 0
            }
        
        return result[0]
    
    async def mark_overdue_accounts(self, ip_address: str = "system") -> int:
        """Marca cuentas vencidas como overdue"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        # Buscar cuentas pendientes vencidas
        result = await db[self.collection].update_many(
            {
                "status": AccountStatus.PENDING,
                "due_date": {"$lt": datetime.utcnow()}
            },
            {
                "$set": {
                    "status": AccountStatus.OVERDUE,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log de auditoría si se actualizaron cuentas
        if result.modified_count > 0:
            await audit_service.log_action(
                user_id=None,
                username="system",
                action="update",
                resource="account",
                details={
                    "operation": "mark_overdue",
                    "accounts_updated": result.modified_count
                },
                ip_address=ip_address
            )
        
        return result.modified_count


# Instancia global del servicio de cuentas
account_service = AccountService()