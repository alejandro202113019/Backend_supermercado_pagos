from fastapi import HTTPException, status


class CustomException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationException(CustomException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationException(CustomException):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundException(CustomException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ValidationException(CustomException):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class DatabaseException(CustomException):
    def __init__(self, message: str = "Database error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordPolicyException(CustomException):
    def __init__(self, message: str = "Password does not meet policy requirements"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)