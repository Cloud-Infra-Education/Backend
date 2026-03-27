"""
Contents Internal API endpoints
Lambda에서 호출하는 내부용 upsert 엔드포인트
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.content import Content

router = APIRouter(prefix="/contents", tags=["Contents-Internal"])


def verify_internal_token(x_internal_token: str = Header(None)):
    """내부 토큰 검증 (공유 시크릿)"""
    from app.core.config import settings
    if not settings.INTERNAL_TOKEN:
        raise HTTPException(status_code=500, detail="INTERNAL_TOKEN not configured")
    if not x_internal_token or x_internal_token != settings.INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid internal token")


@router.put("/{content_id}/upsert-internal", dependencies=[Depends(verify_internal_token)])
def upsert_content_internal(
    content_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Lambda에서 호출하는 내부용 contents upsert 엔드포인트
    payload: {"title": "...", "description": "...", "age_rating": "..."}
    """
    title = payload.get("title")
    description = payload.get("description", "")
    age_rating = payload.get("age_rating", "ALL")

    if not title:
        raise HTTPException(status_code=400, detail="title is required")

    content = db.query(Content).filter(Content.id == content_id).first()
    if content:
        # 기존 content 업데이트
        content.title = title
        content.description = description
        content.age_rating = age_rating
    else:
        # 새 content 생성 (id 명시적으로 지정)
        content = Content(
            id=content_id,
            title=title,
            description=description,
            age_rating=age_rating,
            like_count=0
        )
        db.add(content)

    db.commit()
    db.refresh(content)
    return {"id": content.id, "title": content.title, "age_rating": content.age_rating}
