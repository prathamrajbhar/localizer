"""
Core configuration module - Optimized for production deployment
"""
from pydantic_settings import BaseSettings
from pydantic import validator, Field
from functools import lru_cache
from typing import Dict, List
import os


class Settings(BaseSettings):
    """
    Application settings with validation and optimization
    """
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://username:password@localhost:5432/localizer",
        description="PostgreSQL database connection URL"
    )
    
    # Note: Authentication removed as per requirements
    
    # Storage Configuration
    STORAGE_DIR: str = "storage"
    UPLOAD_DIR: str = "storage/uploads"
    OUTPUT_DIR: str = "storage/outputs"
    MODEL_DIR: str = "models"
    
    # File Upload Limits
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024, description="Max file size in bytes")  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".txt", ".pdf", ".mp3", ".mp4", ".wav", ".docx", ".doc", ".odt", ".rtf"]
    
    # Environment Configuration
    ENVIRONMENT: str = Field(default="production", pattern="^(development|staging|production)$")
    DEBUG: bool = False
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Indian Language Localizer"
    VERSION: str = "1.0.0"
    
    # AI Model Configuration
    TRANSLATION_MODEL: str = "ai4bharat/IndicTrans2-en-indic-1B"
    WHISPER_MODEL: str = "openai/whisper-large-v3"
    TTS_MODEL: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    
    # Performance Configuration
    MODEL_CACHE_SIZE: int = Field(default=3, ge=1, le=10)
    MAX_CONCURRENT_REQUESTS: int = Field(default=10, ge=1, le=100)
    REQUEST_TIMEOUT: int = Field(default=300, ge=30, le=600)  # 30s to 10min
    
    # Note: SECRET_KEY validator removed - no authentication needed
    
    @validator("DEBUG")
    def validate_debug_mode(cls, v, values):
        if v and values.get("ENVIRONMENT") == "production":
            raise ValueError("Debug mode must be disabled in production")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True
        extra = "ignore"  # Ignore extra environment variables


# Supported Languages (22 Indian Languages + English)
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "as": "Assamese",
    "bn": "Bengali",
    "brx": "Bodo",
    "doi": "Dogri",
    "en": "English",  # Added English for language detection
    "gu": "Gujarati",
    "hi": "Hindi",
    "kn": "Kannada",
    "ks": "Kashmiri",
    "kok": "Konkani",
    "mai": "Maithili",
    "ml": "Malayalam",
    "mni": "Manipuri",
    "mr": "Marathi",
    "ne": "Nepali",
    "or": "Odia",
    "pa": "Punjabi",
    "sa": "Sanskrit",
    "sat": "Santali",
    "sd": "Sindhi",
    "ta": "Tamil",
    "te": "Telugu",
    "ur": "Urdu"
}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

