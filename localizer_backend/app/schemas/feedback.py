"""
Feedback schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    translation_id: Optional[int] = Field(None, description="Translation ID if providing feedback on specific translation")
    file_id: Optional[int] = Field(None, description="File ID if providing feedback on file directly")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comments: Optional[str] = Field(None, max_length=2000)
    corrections: Optional[dict] = Field(None, description="JSON with text corrections")
    



class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    model_config = {"from_attributes": True}
    
    id: int
    translation_id: int
    user_id: int
    rating: int
    comments: Optional[str]
    corrections: Optional[str]
    created_at: datetime


class FeedbackStats(BaseModel):
    """Schema for feedback statistics"""
    total_feedback: int
    average_rating: float
    rating_distribution: dict
    top_issues: list

