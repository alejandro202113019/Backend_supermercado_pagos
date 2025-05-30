import base64
from cryptography.fernet import Fernet
from config.settings import settings


class EncryptionService:
    def __init__(self):
        # Asegurarse de que la clave tenga 32 bytes
        key = settings.encryption_key.encode()
        if len(key) < 32:
            key = key.ljust(32, b'0')
        elif len(key) > 32:
            key = key[:32]
        
        # Generar clave válida para Fernet
        self.fernet = Fernet(base64.urlsafe_b64encode(key))
    
    def encrypt(self, data: str) -> str:
        """Cifra una cadena de texto"""
        if not data:
            return data
        
        encrypted_data = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Descifra una cadena de texto"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            # Si no se puede descifrar, retornar el dato original
            return encrypted_data
    
    def encrypt_sensitive_fields(self, document: dict, fields_to_encrypt: list) -> dict:
        """Cifra campos específicos de un documento"""
        encrypted_doc = document.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_doc and encrypted_doc[field]:
                encrypted_doc[field] = self.encrypt(str(encrypted_doc[field]))
        
        return encrypted_doc
    
    def decrypt_sensitive_fields(self, document: dict, fields_to_decrypt: list) -> dict:
        """Descifra campos específicos de un documento"""
        decrypted_doc = document.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_doc and decrypted_doc[field]:
                decrypted_doc[field] = self.decrypt(decrypted_doc[field])
        
        return decrypted_doc


# Instancia global del servicio de cifrado
encryption_service = EncryptionService()