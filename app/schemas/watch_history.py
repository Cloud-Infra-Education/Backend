"""
WatchHistory schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WatchHistoryBase(BaseModel):
    """시청기록 기본 스키마"""
    content_id: int
    last_played_time: float = Field(0.0, ge=0, description="마지막 재생 시간 (초)")


class WatchHistoryCreate(WatchHistoryBase):
    """시청기록 생성용 스키마"""
    pass


class WatchHistoryUpdate(BaseModel):
    """시청기록 수정용 스키마"""
    last_played_time: float = Field(..., ge=0, description="마지막 재생 시간 (초)")


class WatchHistoryResponse(WatchHistoryBase):
    """시청기록 응답 스키마"""
    id: int
    user_id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True
