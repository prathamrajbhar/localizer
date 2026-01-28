"""
File schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class FileUpload(BaseModel):
    """Schema for file upload metadata"""
    domain: Optional[str] = Field(None, description="Domain: healthcare, construction, education, etc.")
    source_language: Optional[str] = Field(None, description="Source language code")


class FileResponse(BaseModel):
    """Schema for file response"""
    model_config = {"from_attributes": True}
    
    id: int
    filename: str
    original_filename: str
    path: str
    file_type: Optional[str]
    size: Optional[int]
    domain: Optional[str]
    source_language: Optional[str]
    created_at: datetime


class FileUploadResponse(BaseModel):
    """Enhanced schema for file upload response with extracted text"""
    model_config = {"from_attributes": True}
    
    id: int
    filename: str
    original_filename: str
    path: str
    file_type: Optional[str]
    size: Optional[int]
    domain: Optional[str]
    source_language: Optional[str]
    created_at: datetime
    extracted_text: Optional[str] = None
    text_metadata: Optional[Dict[str, Any]] = None
    extraction_status: Optional[str] = None


class FileMetadata(BaseModel):
    """Schema for file metadata"""
    file_id: int
    filename: str
    size: int
    file_type: str
    pages: Optional[int] = None
    word_count: Optional[int] = None

