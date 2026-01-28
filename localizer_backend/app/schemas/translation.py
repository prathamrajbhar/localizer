"""
Translation schemas
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from app.core.config import SUPPORTED_LANGUAGES


class TranslationRequest(BaseModel):
    """Schema for translation request"""
    file_id: Optional[int] = None
    text: Optional[str] = Field(None, max_length=50000)
    source_language: str = Field(..., min_length=2, max_length=10)
    target_languages: List[str] = Field(..., min_items=1)
    domain: Optional[str] = Field(None, description="Domain for context adaptation")
    apply_localization: bool = Field(default=True, description="Apply cultural localization")
    
    @validator("source_language")
    def validate_source_language(cls, v):
        if v not in SUPPORTED_LANGUAGES and v != "en":
            raise ValueError(f"Source language '{v}' not supported. Choose from 22 Indian languages or 'en'")
        return v
    
    @validator("target_languages")
    def validate_target_languages(cls, v):
        for lang in v:
            # Allow English ('en') as a valid target in addition to the supported Indian languages
            if lang != "en" and lang not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Target language '{lang}' not supported. Choose from 22 Indian languages or 'en'")
        return v


class TranslationResponse(BaseModel):
    """Schema for direct translation response"""
    model_config = {"protected_namespaces": ()}
    
    target_language: str
    translated_text: str
    confidence: float
    processing_time: float
    model_used: Optional[str] = None
    source_language: Optional[str] = None
    source_language_name: Optional[str] = None
    target_language_name: Optional[str] = None
    domain: Optional[str] = None
    translation_id: Optional[int] = None
    localized: Optional[bool] = False
    error: Optional[str] = None


class BatchTranslationResponse(BaseModel):
    """Schema for batch translation response"""
    results: List[TranslationResponse]
    total_processing_time: float
    localized: bool


class LanguageDetectionResponse(BaseModel):
    """Schema for language detection response"""
    detected_language: str
    language_name: str
    confidence: float


class LocalizationRequest(BaseModel):
    """Schema for localization request"""
    translation_id: int
    domain: str
    cultural_context: Optional[dict] = None

