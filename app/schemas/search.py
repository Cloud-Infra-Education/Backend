"""
Search schemas
검색 관련 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.content import ContentResponse


class SearchRequest(BaseModel):
    """검색 요청 스키마"""
    query: str = Field(..., min_length=1, description="검색어")
    limit: int = Field(20, ge=1, le=100, description="결과 개수 제한")
    offset: int = Field(0, ge=0, description="결과 오프셋")


class SearchResponse(BaseModel):
    """검색 응답 스키마"""
    hits: List[ContentResponse] = Field(..., description="검색 결과")
    query: str = Field(..., description="검색 쿼리")
    processing_time_ms: int = Field(..., description="처리 시간 (밀리초)")
    limit: int = Field(..., description="결과 개수 제한")
    offset: int = Field(..., description="결과 오프셋")
    estimated_total_hits: Optional[int] = Field(None, description="예상 총 결과 수")
