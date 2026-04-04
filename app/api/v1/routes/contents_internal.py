"""
Contents Internal API endpoints
Lambda 함수에서 사용하는 내부 API (인증 토큰 사용)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.content import Content
from app.schemas.content import ContentUpdate, ContentResponse
from app.services.search import search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contents", tags=["Contents Internal"])

INTERNAL_TOKEN = "formation-lap-internal-token-2024-secret-key"  # Lambda와 공유하는 토큰


async def verify_internal_token(x_internal_token: str = Header(..., alias="X-Internal-Token")):
    """내부 토큰 검증"""
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token"
        )
    return True


@router.put("/{content_id}/upsert-internal", response_model=ContentResponse)
async def upsert_content_internal(
    content_id: int,
    content_data: ContentUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_token)
):
    """
    Lambda 함수에서 사용하는 내부 upsert 엔드포인트
    content_id가 있으면 업데이트, 없으면 생성
    """
    # 기존 content 확인
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if content:
        # 업데이트
        if content_data.title is not None:
            content.title = content_data.title
        if content_data.description is not None:
            content.description = content_data.description
        if content_data.age_rating is not None:
            content.age_rating = content_data.age_rating
        
        db.commit()
        db.refresh(content)
        
        logger.info(f"Content updated: id={content_id}, title={content.title}")
    else:
        # 생성
        content = Content(
            id=content_id,
            title=content_data.title or f"Content {content_id}",
            description=content_data.description or "",
            age_rating=content_data.age_rating or "ALL",
            like_count=0
        )
        db.add(content)
        db.commit()
        db.refresh(content)
        
        logger.info(f"Content created: id={content_id}, title={content.title}")
    
    # Meilisearch 인덱스에 동기화
    if search_service.is_available():
        search_doc = {
            "id": content.id,
            "title": content.title,
            "description": content.description or "",
            "age_rating": content.age_rating or "",
            "like_count": content.like_count
        }
        await search_service.sync_content(search_doc)
    
    return content
