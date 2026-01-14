"""
WatchHistory API endpoints
시청기록
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import security, verify_token
from fastapi.security import HTTPAuthorizationCredentials
from app.models.watch_history import WatchHistory
from app.models.content import Content
from app.schemas.watch_history import WatchHistoryCreate, WatchHistoryUpdate, WatchHistoryResponse

router = APIRouter(prefix="/watch-history", tags=["Watch History"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """현재 사용자 정보 추출"""
    payload = await verify_token(credentials)
    return payload


@router.post("", response_model=WatchHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_watch_history(
    history_data: WatchHistoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """시청기록 생성 또는 업데이트"""
    # 컨텐츠 존재 확인
    content = db.query(Content).filter(Content.id == history_data.content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    keycloak_user_id = current_user.get("sub")
    try:
        user_id = int(keycloak_user_id.split("-")[-1][:8], 16) if "-" in keycloak_user_id else 1
    except:
        user_id = 1
    
    # 기존 시청기록 확인
    existing_history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.content_id == history_data.content_id
    ).first()
    
    if existing_history:
        # 업데이트
        existing_history.last_played_time = history_data.last_played_time
        db.commit()
        db.refresh(existing_history)
        return existing_history
    else:
        # 생성
        db_history = WatchHistory(
            user_id=user_id,
            content_id=history_data.content_id,
            last_played_time=history_data.last_played_time
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        return db_history


@router.get("", response_model=List[WatchHistoryResponse])
async def get_watch_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """사용자의 시청기록 목록 조회"""
    keycloak_user_id = current_user.get("sub")
    try:
        user_id = int(keycloak_user_id.split("-")[-1][:8], 16) if "-" in keycloak_user_id else 1
    except:
        user_id = 1
    
    histories = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id
    ).offset(skip).limit(limit).order_by(WatchHistory.updated_at.desc()).all()
    
    return histories


@router.get("/{content_id}", response_model=WatchHistoryResponse)
async def get_watch_history_by_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """특정 컨텐츠의 시청기록 조회"""
    keycloak_user_id = current_user.get("sub")
    try:
        user_id = int(keycloak_user_id.split("-")[-1][:8], 16) if "-" in keycloak_user_id else 1
    except:
        user_id = 1
    
    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.content_id == content_id
    ).first()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch history not found"
        )
    
    return history


@router.put("/{content_id}", response_model=WatchHistoryResponse)
async def update_watch_history(
    content_id: int,
    history_data: WatchHistoryUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """시청기록 수정"""
    keycloak_user_id = current_user.get("sub")
    try:
        user_id = int(keycloak_user_id.split("-")[-1][:8], 16) if "-" in keycloak_user_id else 1
    except:
        user_id = 1
    
    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.content_id == content_id
    ).first()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch history not found"
        )
    
    history.last_played_time = history_data.last_played_time
    db.commit()
    db.refresh(history)
    return history


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watch_history(
    content_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """시청기록 삭제"""
    keycloak_user_id = current_user.get("sub")
    try:
        user_id = int(keycloak_user_id.split("-")[-1][:8], 16) if "-" in keycloak_user_id else 1
    except:
        user_id = 1
    
    history = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.content_id == content_id
    ).first()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch history not found"
        )
    
    db.delete(history)
    db.commit()
    return None
