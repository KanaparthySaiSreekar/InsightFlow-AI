from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "InsightFlow AI"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: str  # Fernet key for encrypting API keys

    # Database
    DATABASE_URL: str

    # DuckDB
    DUCKDB_PATH: str = "./data/duckdb_files"

    # File Upload
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 1073741824  # 1GB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls", ".json", ".sqlite"]

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
os.makedirs(settings.DUCKDB_PATH, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
