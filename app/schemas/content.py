"""
Content schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ContentBase(BaseModel):
    """컨텐츠 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    age_rating: Optional[str] = Field(None, description="연령 등급 (예: ALL, 12, 15, 18)")


class ContentCreate(ContentBase):
    """컨텐츠 생성용 스키마"""
    pass


class ContentUpdate(BaseModel):
    """컨텐츠 수정용 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    age_rating: Optional[str] = None


class ContentResponse(ContentBase):
    """컨텐츠 응답 스키마"""
    id: int
    like_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
