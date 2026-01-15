"""
ContentLike schemas
"""
from pydantic import BaseModel
from datetime import datetime


class ContentLikeResponse(BaseModel):
    """좋아요 응답 스키마"""
    id: int
    user_id: int
    contents_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
