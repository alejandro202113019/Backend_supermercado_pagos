from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    mongodb_url: str
    database_name: str
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Encryption
    encryption_key: str
    
    # App
    debug: bool = False
    app_name: str = "Supermarket Payment System"
    version: str = "1.0.0"
    
    class Config:
        env_file = ".env"


settings = Settings()