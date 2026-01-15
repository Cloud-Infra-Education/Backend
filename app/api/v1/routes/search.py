"""
Search API endpoints
검색 API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.search import search_service
from app.schemas.search import SearchResponse
from app.schemas.content import ContentResponse
from app.models.content import Content

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
async def search_contents(
    q: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(20, ge=1, le=100, description="결과 개수 제한"),
    offset: int = Query(0, ge=0, description="결과 오프셋"),
    db: Session = Depends(get_db)
):
    """
    콘텐츠 검색
    
    Meilisearch를 사용하여 콘텐츠를 검색합니다.
    """
    if not search_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service is not available"
        )
    
    try:
        # Meilisearch 검색 수행
        results = await search_service.search_contents(q, limit, offset)
        
        # 검색 결과에서 문서 ID 추출
        hit_ids = [hit.get("id") for hit in results.get("hits", []) if "id" in hit]
        
        # DB에서 실제 콘텐츠 데이터 조회 (순서 유지)
        # DB 연결 실패 시에도 Meilisearch 결과만 반환
        contents_dict = {}
        if hit_ids:
            try:
                contents = db.query(Content).filter(Content.id.in_(hit_ids)).all()
                contents_dict = {content.id: content for content in contents}
            except Exception:
                # DB 연결 실패 시 Meilisearch 결과만 반환
                pass
        
        # Meilisearch 결과 순서대로 콘텐츠 매핑
        hits = []
        for hit in results.get("hits", []):
            content_id = hit.get("id")
            if content_id in contents_dict:
                hits.append(contents_dict[content_id])
            else:
                # DB에서 조회 실패 시 Meilisearch 결과를 직접 사용
                # ContentResponse 형식으로 변환
                from app.schemas.content import ContentResponse
                hits.append(ContentResponse(
                    id=hit.get("id", 0),
                    title=hit.get("title", ""),
                    description=hit.get("description", ""),
                    age_rating=hit.get("age_rating", "ALL"),
                    like_count=hit.get("like_count", 0),
                    created_at=hit.get("created_at", None)
                ))
        
        return SearchResponse(
            hits=hits,
            query=q,
            processing_time_ms=results.get("processingTimeMs", 0),
            limit=limit,
            offset=offset,
            estimated_total_hits=results.get("estimatedTotalHits")
        )
    except ValueError as e:
        error_str = str(e)
        # 인덱스가 없을 때는 빈 결과 반환
        if "index_not_found" in error_str.lower():
            return SearchResponse(
                hits=[],
                query=q,
                processing_time_ms=0,
                limit=limit,
                offset=offset,
                estimated_total_hits=0
            )
        # 그 외의 오류는 다시 raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {error_str}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
