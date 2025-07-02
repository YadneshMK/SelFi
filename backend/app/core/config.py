from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Financial Investment Tracker"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./finance_app.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # APIs
    ALPHA_VANTAGE_API_KEY: str = ""
    MF_API_BASE_URL: str = "https://api.mfapi.in/mf"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_PATH: str = "./uploads"
    
    # Email
    EMAIL_HOST: str = "imap.gmail.com"
    EMAIL_PORT: int = 993
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)