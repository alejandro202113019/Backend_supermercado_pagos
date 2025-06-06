import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import os

# Asegúrate de que estas importaciones sean correctas para tu modelo
from models.audit import AuditLog, SessionLog, AuditAction, AuditLevel  # Importar correctamente AuditLevel
from schemas.audit import AuditSearchFilters


class AuditService:
    def __init__(self):
        self.audit_log_file = "audit_log.txt"  # Archivo para guardar los logs
        self.session_collection = "session_logs"

    def log_to_file(self, log_message: str):
        """Función que guarda el mensaje en un archivo de texto"""
        try:
            with open(self.audit_log_file, "a") as file:
                file.write(log_message + "\n")
        except Exception as e:
            print(f"Error escribiendo el log en archivo: {e}")

    async def log_action(
            self,
            user_id: Optional[str],
            username: Optional[str],
            action: AuditAction,
            resource: str,
            resource_id: Optional[str] = None,
            details: Dict[str, Any] = None,
            ip_address: str = "unknown",
            user_agent: Optional[str] = None,
            level: AuditLevel = AuditLevel.INFO,  # Uso correcto de AuditLevel
            success: bool = True,
            error_message: Optional[str] = None,
            session_id: Optional[str] = None
    ):
        print("Entro al log de auditoria")
        """Registra una acción en el log de auditoría"""
        try:
            log_message = f"{datetime.utcnow()} - ACTION: {action} - USER: {username} - RESOURCE: {resource} - " \
                          f"RESOURCE_ID: {resource_id} - SUCCESS: {success} - IP: {ip_address} - SESSION_ID: {session_id} - " \
                          f"DETAILS: {details or {} } - ERROR: {error_message if error_message else 'None'}"

            # Log en archivo de texto
            self.log_to_file(log_message)

            print("Log registrado en archivo:", log_message)

        except Exception as e:
            print(f"Error en auditoría: {e}")

    async def log_login(
            self,
            user_id: str,
            username: str,
            ip_address: str,
            user_agent: Optional[str] = None,
            success: bool = True,
            error_message: Optional[str] = None
    ) -> str:
        """Registra un intento de login y crea/actualiza sesión"""
        session_id = str(uuid.uuid4())

        try:
            # Registrar en log de auditoría
            await self.log_action(
                user_id=user_id if success else None,
                username=username,
                action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
                resource="auth",
                ip_address=ip_address,
                user_agent=user_agent,
                level=AuditLevel.INFO if success else AuditLevel.WARNING,
                success=success,
                error_message=error_message,
                session_id=session_id
            )

        except Exception as e:
            print(f"Error en log_login: {e}")

        return session_id

    async def log_logout(
            self,
            user_id: str,
            username: str,
            session_id: str,
            ip_address: str
    ):
        """Registra logout y cierra sesión"""
        try:
            log_message = f"{datetime.utcnow()} - LOGOUT - USER: {username} - SESSION_ID: {session_id} - IP: {ip_address}"

            # Log en archivo de texto
            self.log_to_file(log_message)

            print("Log de logout registrado:", log_message)

        except Exception as e:
            print(f"Error en log_logout: {e}")

    async def update_session_activity(self, session_id: str):
        """Actualiza la última actividad de la sesión"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()

            if db is None:
                print("Error: Database is None in audit_service.update_session_activity")
                return

            await db[self.session_collection].update_one(
                {"session_id": session_id, "is_active": True},
                {"$set": {"last_activity": datetime.utcnow()}}
            )

        except Exception as e:
            print(f"Error actualizando actividad de sesión: {e}")

    async def get_audit_logs(
            self,
            filters: AuditSearchFilters,
            page: int = 1,
            size: int = 50
    ) -> Dict[str, Any]:
        """Obtiene logs de auditoría con filtros"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()

            if db is None:
                print("Error: Database is None in audit_service.get_audit_logs")
                return {
                    "logs": [],
                    "total": 0,
                    "page": page,
                    "size": size
                }

            # Construir query
            query = {}
            if filters.user_id:
                query["user_id"] = filters.user_id
            if filters.action:
                query["action"] = filters.action
            if filters.resource:
                query["resource"] = filters.resource
            if filters.level:
                query["level"] = filters.level
            if filters.success is not None:
                query["success"] = filters.success
            if filters.ip_address:
                query["ip_address"] = filters.ip_address

            # Filtros de fecha
            if filters.date_from or filters.date_to:
                date_query = {}
                if filters.date_from:
                    date_query["$gte"] = filters.date_from
                if filters.date_to:
                    date_query["$lte"] = filters.date_to
                query["timestamp"] = date_query

            # Contar total
            total = await db[self.audit_collection].count_documents(query)

            # Obtener logs paginados
            skip = (page - 1) * size
            cursor = db[self.audit_collection].find(query).sort("timestamp", -1).skip(skip).limit(size)
            logs = await cursor.to_list(length=size)

            return {
                "logs": logs,
                "total": total,
                "page": page,
                "size": size
            }

        except Exception as e:
            print(f"Error obteniendo audit logs: {e}")
            return {
                "logs": [],
                "total": 0,
                "page": page,
                "size": size
            }

    async def get_active_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene sesiones activas"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()

            if db is None:
                print("Error: Database is None in audit_service.get_active_sessions")
                return []

            query = {"is_active": True}
            if user_id:
                query["user_id"] = user_id

            cursor = db[self.session_collection].find(query).sort("login_time", -1)
            sessions = await cursor.to_list(length=None)

            return sessions
        except Exception as e:
            print(f"Error obteniendo sesiones activas: {e}")
            return []

    async def force_logout_session(self, session_id: str) -> bool:
        """Fuerza el cierre de una sesión"""
        try:
            db: AsyncIOMotorDatabase = await self.get_database()

            if db is None:
                print("Error: Database is None in audit_service.force_logout_session")
                return False

            result = await db[self.session_collection].update_one(
                {"session_id": session_id, "is_active": True},
                {"$set": {"is_active": False, "logout_time": datetime.utcnow()}}
            )

            return result.modified_count > 0

        except Exception as e:
            print(f"Error forzando logout: {e}")
            return False


# Instancia global del servicio de auditoría
audit_service = AuditService()
