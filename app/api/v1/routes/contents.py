"""
Contents API endpoints
컨텐츠 CRUD
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import security, verify_token
from fastapi.security import HTTPAuthorizationCredentials
from app.models.content import Content
from app.schemas.content import ContentCreate, ContentUpdate, ContentResponse

router = APIRouter(prefix="/contents", tags=["Contents"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """현재 사용자 정보 추출"""
    return await verify_token(credentials)


@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """컨텐츠 생성"""
    db_content = Content(
        title=content_data.title,
        description=content_data.description,
        age_rating=content_data.age_rating,
        like_count=0
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


@router.get("", response_model=List[ContentResponse])
async def list_contents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """컨텐츠 목록 조회"""
    contents = db.query(Content).offset(skip).limit(limit).all()
    return contents


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: int,
    db: Session = Depends(get_db)
):
    """컨텐츠 상세 조회"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    return content


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    content_data: ContentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """컨텐츠 수정"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    if content_data.title is not None:
        content.title = content_data.title
    if content_data.description is not None:
        content.description = content_data.description
    if content_data.age_rating is not None:
        content.age_rating = content_data.age_rating
    
    db.commit()
    db.refresh(content)
    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """컨텐츠 삭제"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    db.delete(content)
    db.commit()
    return None
