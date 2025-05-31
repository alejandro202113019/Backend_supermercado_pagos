from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from models.user import User, UserRole, UserStatus
from schemas.user import UserCreate, UserUpdate, UserResponse
from utils.security import get_password_hash
from utils.validators import validate_password_policy, validate_email
from utils.exceptions import ValidationException, NotFoundException
from services.encryption_service import encryption_service


class UserService:
    def __init__(self):
        self.collection = "users"
    
    async def get_database(self):
        """Obtiene la base de datos - importación diferida para evitar circular imports"""
        from config.database import get_database
        return await get_database()
    
    async def get_audit_service(self):
        """Obtiene el servicio de auditoría - importación diferida"""
        from services.audit_service import audit_service
        return audit_service
    
    def _prepare_user_from_doc(self, user_doc: dict, include_password: bool = False) -> User:
        """Prepara un objeto User desde un documento de MongoDB"""
        # Crear una copia del documento
        doc_copy = user_doc.copy()
        
        # Convertir _id a string si es ObjectId
        if '_id' in doc_copy and isinstance(doc_copy['_id'], ObjectId):
            doc_copy['_id'] = str(doc_copy['_id'])
        
        # Si no incluimos password, agregar un hash dummy para que pase la validación
        if not include_password and 'hashed_password' not in doc_copy:
            doc_copy['hashed_password'] = "dummy_hash"
        
        # Descifrar campos sensibles
        doc_copy = encryption_service.decrypt_sensitive_fields(
            doc_copy, 
            ["phone", "address"]
        )
        
        return User(**doc_copy)
    
    async def create_user(
        self,
        user_data: UserCreate,
        created_by_id: str,
        ip_address: str
    ) -> User:
        """Crea un nuevo usuario"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()
            audit_service = await self.get_audit_service()
            
            # Validaciones
            validate_email(user_data.email)
            validate_password_policy(user_data.password)
            
            # Verificar duplicados
            existing_email = await db[self.collection].find_one({"email": user_data.email})
            if existing_email:
                raise ValidationException("El email ya está registrado")
            
            existing_username = await db[self.collection].find_one({"username": user_data.username})
            if existing_username:
                raise ValidationException("El nombre de usuario ya está en uso")
            
            # Crear usuario
            user = User(
                email=user_data.email,
                username=user_data.username,
                full_name=user_data.full_name,
                phone=user_data.phone,
                address=user_data.address,
                role=user_data.role,
                hashed_password=get_password_hash(user_data.password)
            )
            
            # Cifrar campos sensibles
            user_doc = user.dict(by_alias=True, exclude={"id"})
            user_doc = encryption_service.encrypt_sensitive_fields(
                user_doc, 
                ["phone", "address"]
            )
            
            # Insertar en base de datos
            result = await db[self.collection].insert_one(user_doc)
            user.id = str(result.inserted_id)
            
            # Log de auditoría con acción válida
            await audit_service.log_action(
                user_id=created_by_id,
                username="admin",
                action="create",  # Acción válida
                resource="user",
                resource_id=str(user.id),
                details={
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                    "created_by": created_by_id
                },
                ip_address=ip_address
            )
            
            return user
            
        except ValidationException:
            raise
        except Exception as e:
            print(f"Error en create_user: {e}")
            import traceback
            traceback.print_exc()
            raise ValidationException("Error interno al crear usuario")
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Obtiene un usuario por ID"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()
            
            if not ObjectId.is_valid(user_id):
                raise ValidationException("ID de usuario inválido")
            
            user_doc = await db[self.collection].find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                raise NotFoundException("Usuario no encontrado")
            
            return self._prepare_user_from_doc(user_doc, include_password=True)
            
        except (ValidationException, NotFoundException):
            raise
        except Exception as e:
            print(f"Error en get_user_by_id: {e}")
            import traceback
            traceback.print_exc()
            raise NotFoundException("Error interno al obtener usuario")
    
    async def update_user(
        self,
        user_id: str,
        user_data: UserUpdate,
        updated_by_id: str,
        ip_address: str
    ) -> User:
        """Actualiza un usuario"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()
            audit_service = await self.get_audit_service()
            
            if not ObjectId.is_valid(user_id):
                raise ValidationException("ID de usuario inválido")
            
            # Verificar que el usuario existe
            existing_user = await db[self.collection].find_one({"_id": ObjectId(user_id)})
            if not existing_user:
                raise NotFoundException("Usuario no encontrado")
            
            # Preparar datos de actualización
            update_data = {}
            original_data = {}
            
            # Solo actualizar campos proporcionados
            if user_data.email is not None:
                validate_email(user_data.email)
                # Verificar que el email no esté en uso por otro usuario
                existing_email = await db[self.collection].find_one({
                    "email": user_data.email,
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_email:
                    raise ValidationException("El email ya está registrado")
                update_data["email"] = user_data.email
                original_data["email"] = existing_user.get("email")
            
            if user_data.username is not None:
                # Verificar que el username no esté en uso por otro usuario
                existing_username = await db[self.collection].find_one({
                    "username": user_data.username,
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_username:
                    raise ValidationException("El nombre de usuario ya está en uso")
                update_data["username"] = user_data.username
                original_data["username"] = existing_user.get("username")
            
            if user_data.full_name is not None:
                update_data["full_name"] = user_data.full_name
                original_data["full_name"] = existing_user.get("full_name")
            
            if user_data.phone is not None:
                update_data["phone"] = encryption_service.encrypt(user_data.phone)
                original_data["phone"] = existing_user.get("phone")
            
            if user_data.address is not None:
                update_data["address"] = encryption_service.encrypt(user_data.address)
                original_data["address"] = existing_user.get("address")
            
            if user_data.role is not None:
                update_data["role"] = user_data.role
                original_data["role"] = existing_user.get("role")
            
            if user_data.status is not None:
                update_data["status"] = user_data.status
                original_data["status"] = existing_user.get("status")
            
            if not update_data:
                raise ValidationException("No hay datos para actualizar")
            
            update_data["updated_at"] = datetime.utcnow()
            
            # Actualizar en base de datos
            await db[self.collection].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            # Log de auditoría con acción válida
            await audit_service.log_action(
                user_id=updated_by_id,
                username="admin",
                action="update",  # Acción válida
                resource="user",
                resource_id=user_id,
                details={
                    "updated_fields": list(update_data.keys()),
                    "original_data": original_data,
                    "updated_by": updated_by_id
                },
                ip_address=ip_address
            )
            
            # Obtener usuario actualizado
            return await self.get_user_by_id(user_id)
            
        except (ValidationException, NotFoundException):
            raise
        except Exception as e:
            print(f"Error en update_user: {e}")
            import traceback
            traceback.print_exc()
            raise ValidationException("Error interno al actualizar usuario")
    
    async def delete_user(
        self,
        user_id: str,
        deleted_by_id: str,
        ip_address: str
    ) -> bool:
        """Elimina un usuario (soft delete)"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()
            audit_service = await self.get_audit_service()
            
            if not ObjectId.is_valid(user_id):
                raise ValidationException("ID de usuario inválido")
            
            # Verificar que el usuario existe
            existing_user = await db[self.collection].find_one({"_id": ObjectId(user_id)})
            if not existing_user:
                raise NotFoundException("Usuario no encontrado")
            
            # Soft delete - cambiar estado a inactivo
            await db[self.collection].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "status": UserStatus.INACTIVE,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Log de auditoría con acción válida
            await audit_service.log_action(
                user_id=deleted_by_id,
                username="admin",
                action="delete",  # Acción válida
                resource="user",
                resource_id=user_id,
                details={
                    "email": existing_user.get("email"),
                    "username": existing_user.get("username"),
                    "deleted_by": deleted_by_id
                },
                ip_address=ip_address
            )
            
            return True
            
        except (ValidationException, NotFoundException):
            raise
        except Exception as e:
            print(f"Error en delete_user: {e}")
            import traceback
            traceback.print_exc()
            raise ValidationException("Error interno al eliminar usuario")
    
    async def get_users(
        self,
        page: int = 1,
        size: int = 50,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene lista de usuarios con paginación y filtros"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()
            
            # Construir query
            query = {}
            
            if role:
                query["role"] = role
            
            if status:
                query["status"] = status
            
            if search:
                query["$or"] = [
                    {"full_name": {"$regex": search, "$options": "i"}},
                    {"email": {"$regex": search, "$options": "i"}},
                    {"username": {"$regex": search, "$options": "i"}}
                ]
            
            # Contar total
            total = await db[self.collection].count_documents(query)
            
            # Obtener usuarios paginados - INCLUYENDO hashed_password
            skip = (page - 1) * size
            cursor = db[self.collection].find(query).sort("created_at", -1).skip(skip).limit(size)
            
            users_docs = await cursor.to_list(length=size)
            
            # Convertir a response SIN incluir password
            users = []
            for user_doc in users_docs:
                # Crear documento sin password para el response
                user_doc_safe = {k: v for k, v in user_doc.items() if k != 'hashed_password'}
                user = self._prepare_user_from_doc(user_doc_safe, include_password=False)
                users.append(UserResponse(
                    id=str(user.id),
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name,
                    phone=user.phone,
                    address=user.address,
                    role=user.role,
                    status=user.status,
                    created_at=user.created_at,
                    last_login=user.last_login
                ))
            
            return {
                "users": users,
                "total": total,
                "page": page,
                "size": size
            }
            
        except Exception as e:
            print(f"Error en get_users: {e}")
            import traceback
            traceback.print_exc()
            return {
                "users": [],
                "total": 0,
                "page": page,
                "size": size
            }
    
    async def get_clients(self) -> List[UserResponse]:
        """Obtiene lista de todos los clientes activos"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()
            
            cursor = db[self.collection].find(
                {
                    "role": UserRole.CLIENT,
                    "status": UserStatus.ACTIVE
                }
            ).sort("full_name", 1)
            
            users_docs = await cursor.to_list(length=None)
            
            clients = []
            for user_doc in users_docs:
                # Crear documento sin password para el response
                user_doc_safe = {k: v for k, v in user_doc.items() if k != 'hashed_password'}
                user = self._prepare_user_from_doc(user_doc_safe, include_password=False)
                clients.append(UserResponse(
                    id=str(user.id),
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name,
                    phone=user.phone,
                    address=user.address,
                    role=user.role,
                    status=user.status,
                    created_at=user.created_at,
                    last_login=user.last_login
                ))
            
            return clients
            
        except Exception as e:
            print(f"Error en get_clients: {e}")
            import traceback
            traceback.print_exc()
            return []


# Instancia global del servicio de usuarios
user_service = UserService()