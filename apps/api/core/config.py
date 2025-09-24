import os
from typing import Optional
from dotenv import load_dotenv

# Charger le .env
load_dotenv()  # lit automatiquement le fichier .env à la racine

class Settings:
    # App Configuration
    APP_NAME: str = os.getenv("APP_NAME", "SecretHawk API")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./secrethawk.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", 1))
    
    # File Upload
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", 50 * 1024 * 1024))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/secrethawk")
    
    # Scanning
    SCAN_TIMEOUT: int = int(os.getenv("SCAN_TIMEOUT", 300))
    MAX_CONCURRENT_SCANS: int = int(os.getenv("MAX_CONCURRENT_SCANS", 5))
    
    # Redis (for production)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    # Frontend URL
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Base URL for webhooks
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Discord webhook URL (global default)
    DISCORD_WEBHOOK_URL: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL")
    
    # Gitleaks
    GITLEAKS_PATH: str = os.getenv("GITLEAKS_PATH", "/usr/local/bin/gitleaks")
    
    def __init__(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

settings = Settings()
