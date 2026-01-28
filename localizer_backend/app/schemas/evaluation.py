"""
Evaluation schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EvaluationRequest(BaseModel):
    """Schema for evaluation request"""
    translation_id: int
    reference_text: str = Field(..., description="Ground truth/reference translation")
    hypothesis_text: Optional[str] = Field(None, description="If not provided, uses translation output")
    language_pair: str = Field(..., description="e.g., 'en-hi'")


class EvaluationCreate(BaseModel):
    """Schema for creating evaluation"""
    translation_id: int
    reference_text: str = Field(..., description="Ground truth/reference translation")


class EvaluationResponse(BaseModel):
    """Schema for evaluation response"""
    model_config = {"protected_namespaces": (), "from_attributes": True}
    
    id: int
    translation_id: int
    bleu_score: float
    comet_score: float
    reference_text: str
    evaluator_id: int
    created_at: datetime


class RetrainingRequest(BaseModel):
    """Schema for retraining request"""
    model_config = {"protected_namespaces": ()}
    
    model_name: str = Field(..., description="Model to retrain")
    domain: Optional[str] = Field(None, description="Domain to focus on")
    epochs: int = Field(3, ge=1, le=10)
    min_bleu_threshold: Optional[float] = Field(None, description="Minimum BLEU score to trigger retraining")


class RetrainingResponse(BaseModel):
    """Schema for retraining response"""
    model_config = {"protected_namespaces": ()}
    
    status: str
    message: str
    model_name: str
    started_at: datetime

