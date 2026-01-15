"""
ContentLikes API endpoints
컨텐츠 좋아요
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.core.security import security, verify_token
from fastapi.security import HTTPAuthorizationCredentials
from app.models.content_like import ContentLike
from app.models.content import Content
from app.schemas.content_like import ContentLikeResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/contents/{content_id}/likes", tags=["Content Likes"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """현재 사용자 정보 추출"""
    payload = await verify_token(credentials)
    # Keycloak user_id를 DB user_id로 변환 필요
    # 현재는 Keycloak user_id를 그대로 사용 (추후 매핑 테이블 필요)
    return payload


@router.post("", response_model=ContentLikeResponse, status_code=status.HTTP_201_CREATED)
async def like_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """컨텐츠 좋아요"""
    # 컨텐츠 존재 확인
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # JWT에서 email을 사용하여 DB user_id 가져오기
    user_id = UserService.get_user_id_from_jwt(db, current_user)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database. Please register first."
        )
    
    # 이미 좋아요한 경우 확인
    existing_like = db.query(ContentLike).filter(
        ContentLike.user_id == user_id,
        ContentLike.contents_id == content_id
    ).first()
    
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already liked this content"
        )
    
    # 좋아요 생성
    db_like = ContentLike(
        user_id=user_id,
        contents_id=content_id
    )
    
    try:
        db.add(db_like)
        # 좋아요 수 증가
        content.like_count += 1
        db.commit()
        db.refresh(db_like)
        return db_like
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to like content"
        )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """컨텐츠 좋아요 취소"""
    # JWT에서 email을 사용하여 DB user_id 가져오기
    user_id = UserService.get_user_id_from_jwt(db, current_user)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in database. Please register first."
        )
    
    like = db.query(ContentLike).filter(
        ContentLike.user_id == user_id,
        ContentLike.contents_id == content_id
    ).first()
    
    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Like not found"
        )
    
    content = db.query(Content).filter(Content.id == content_id).first()
    if content and content.like_count > 0:
        content.like_count -= 1
    
    db.delete(like)
    db.commit()
    return None


@router.get("", response_model=List[ContentLikeResponse])
async def get_content_likes(
    content_id: int,
    db: Session = Depends(get_db)
):
    """컨텐츠 좋아요 목록 조회"""
    likes = db.query(ContentLike).filter(ContentLike.contents_id == content_id).all()
    return likes
