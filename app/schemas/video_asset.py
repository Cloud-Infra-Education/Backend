"""
VideoAsset schemas
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class VideoAssetBase(BaseModel):
    """영상 파일 정보 기본 스키마"""
    content_id: int
    video_url: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="썸네일 URL")
    duration: Optional[float] = Field(None, ge=0, description="영상 길이 (초)")


class VideoAssetCreate(VideoAssetBase):
    """영상 파일 정보 생성용 스키마"""
    pass


class VideoAssetUpdate(BaseModel):
    """영상 파일 정보 수정용 스키마"""
    video_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    duration: Optional[float] = Field(None, ge=0)


class VideoAssetResponse(VideoAssetBase):
    """영상 파일 정보 응답 스키마"""
    id: int
    
    class Config:
        from_attributes = True
