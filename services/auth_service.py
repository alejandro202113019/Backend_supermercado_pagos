from datetime import datetime, timedelta
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import User, UserRole, UserStatus
from schemas.auth import LoginRequest, RegisterRequest, ChangePasswordRequest
from utils.security import verify_password, get_password_hash, create_access_token
from utils.validators import validate_password_policy, validate_email
from utils.exceptions import AuthenticationException, ValidationException, NotFoundException
from services.encryption_service import encryption_service
from config.settings import settings


class AuthService:
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
    
    async def authenticate_user(
        self,
        login_data: LoginRequest,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> tuple[User, str]:
        """Autentica un usuario y retorna el usuario y token"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        # Buscar usuario por email
        user_doc = await db[self.collection].find_one({"email": login_data.email})
        
        if not user_doc:
            await audit_service.log_login(
                user_id=None,
                username=login_data.email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="Usuario no encontrado"
            )
            raise AuthenticationException("Credenciales inválidas")
        
        user = User(**user_doc)
        
        # Verificar estado del usuario
        if user.status != UserStatus.ACTIVE:
            await audit_service.log_login(
                user_id=str(user.id),
                username=user.username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=f"Usuario {user.status}"
            )
            raise AuthenticationException(f"Usuario {user.status}")
        
        # Verificar contraseña
        if not verify_password(login_data.password, user.hashed_password):
            # Incrementar intentos fallidos
            await db[self.collection].update_one(
                {"_id": user.id},
                {
                    "$set": {"last_failed_login": datetime.utcnow()},
                    "$inc": {"failed_login_attempts": 1}
                }
            )
            
            await audit_service.log_login(
                user_id=str(user.id),
                username=user.username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="Contraseña incorrecta"
            )
            raise AuthenticationException("Credenciales inválidas")
        
        # Login exitoso
        session_id = await audit_service.log_login(
            user_id=str(user.id),
            username=user.username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        # Actualizar último login y resetear intentos fallidos
        await db[self.collection].update_one(
            {"_id": user.id},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "failed_login_attempts": 0
                }
            }
        )
        
        # Crear token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "role": user.role,
                "session_id": session_id
            },
            expires_delta=access_token_expires
        )
        
        return user, access_token
    
    async def register_user(
        self,
        register_data: RegisterRequest,
        ip_address: str,
        created_by_role: UserRole = UserRole.ADMIN
    ) -> User:
        """Registra un nuevo usuario"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        # Validar email
        validate_email(register_data.email)
        
        # Validar política de contraseñas
        validate_password_policy(register_data.password)
        
        # Verificar si el email ya existe
        existing_user = await db[self.collection].find_one({"email": register_data.email})
        if existing_user:
            raise ValidationException("El email ya está registrado")
        
        # Verificar si el username ya existe
        existing_username = await db[self.collection].find_one({"username": register_data.username})
        if existing_username:
            raise ValidationException("El nombre de usuario ya está en uso")
        
        # Crear usuario
        user = User(
            email=register_data.email,
            username=register_data.username,
            full_name=register_data.full_name,
            phone=register_data.phone,
            address=register_data.address,
            hashed_password=get_password_hash(register_data.password),
            role=UserRole.CLIENT  # Por defecto los nuevos usuarios son clientes
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
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=None,
            username="system",
            action="create",
            resource="user",
            resource_id=str(user.id),
            details={"email": user.email, "username": user.username, "role": user.role},
            ip_address=ip_address
        )
        
        return user
    
    async def change_password(
        self,
        user_id: str,
        change_data: ChangePasswordRequest,
        ip_address: str
    ) -> bool:
        """Cambia la contraseña de un usuario"""
        db: AsyncIOMotorDatabase = await self.get_database()
        audit_service = await self.get_audit_service()
        
        # Obtener usuario actual
        user_doc = await db[self.collection].find_one({"_id": user_id})
        if not user_doc:
            raise NotFoundException("Usuario no encontrado")
        
        user = User(**user_doc)
        
        # Verificar contraseña actual
        if not verify_password(change_data.current_password, user.hashed_password):
            await audit_service.log_action(
                user_id=user_id,
                username=user.username,
                action="password_change",
                resource="user",
                resource_id=user_id,
                ip_address=ip_address,
                success=False,
                error_message="Contraseña actual incorrecta"
            )
            raise AuthenticationException("Contraseña actual incorrecta")
        
        # Validar nueva contraseña
        validate_password_policy(change_data.new_password)
        
        # Actualizar contraseña
        new_hashed_password = get_password_hash(change_data.new_password)
        
        await db[self.collection].update_one(
            {"_id": user_id},
            {
                "$set": {
                    "hashed_password": new_hashed_password,
                    "password_changed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log de auditoría
        await audit_service.log_action(
            user_id=user_id,
            username=user.username,
            action="password_change",
            resource="user",
            resource_id=user_id,
            ip_address=ip_address,
            success=True
        )
        
        return True
    
    async def get_current_user(self, user_id: str) -> User:
        """Obtiene el usuario actual por ID"""
        db: AsyncIOMotorDatabase = await self.get_database()
        
        user_doc = await db[self.collection].find_one({"_id": user_id})
        if not user_doc:
            raise NotFoundException("Usuario no encontrado")
        
        # Descifrar campos sensibles
        user_doc = encryption_service.decrypt_sensitive_fields(
            user_doc, 
            ["phone", "address"]
        )
        
        return User(**user_doc)


# Instancia global del servicio de autenticación
auth_service = AuthService()