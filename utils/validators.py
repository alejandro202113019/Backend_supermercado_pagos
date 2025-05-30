import re
from typing import List
from utils.exceptions import PasswordPolicyException, ValidationException


def validate_password_policy(password: str) -> bool:
    """
    Valida que la contraseña cumpla con las políticas de seguridad:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial
    """
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not re.search(r"[A-Z]", password):
        errors.append("La contraseña debe contener al menos una letra mayúscula")
    
    if not re.search(r"[a-z]", password):
        errors.append("La contraseña debe contener al menos una letra minúscula")
    
    if not re.search(r"\d", password):
        errors.append("La contraseña debe contener al menos un número")
    
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        errors.append("La contraseña debe contener al menos un carácter especial")
    
    if errors:
        raise PasswordPolicyException("; ".join(errors))
    
    return True


def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationException("Formato de email inválido")
    return True


def validate_phone(phone: str) -> bool:
    """Valida formato de teléfono"""
    pattern = r'^\+?[\d\s\-\(\)]{10,15}$'
    if not re.match(pattern, phone):
        raise ValidationException("Formato de teléfono inválido")
    return True


def sanitize_string(value: str) -> str:
    """Sanitiza strings para prevenir inyecciones"""
    if not isinstance(value, str):
        return value
    
    # Remover caracteres potencialmente peligrosos
    dangerous_chars = ['<', '>', '"', "'", '&', '$', '`', '|', ';']
    for char in dangerous_chars:
        value = value.replace(char, '')
    
    return value.strip()


def validate_positive_number(value: float, field_name: str = "value") -> bool:
    """Valida que un número sea positivo"""
    if value <= 0:
        raise ValidationException(f"{field_name} debe ser un número positivo")
    return True


def validate_required_fields(data: dict, required_fields: List[str]) -> bool:
    """Valida que los campos requeridos estén presentes"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationException(f"Campos requeridos faltantes: {', '.join(missing_fields)}")
    
    return True