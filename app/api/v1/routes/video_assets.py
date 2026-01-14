"""
VideoAssets API endpoints
영상 파일 정보
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import security, verify_token
from fastapi.security import HTTPAuthorizationCredentials
from app.models.video_asset import VideoAsset
from app.models.content import Content
from app.schemas.video_asset import VideoAssetCreate, VideoAssetUpdate, VideoAssetResponse

router = APIRouter(prefix="/contents/{content_id}/video-assets", tags=["Video Assets"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """현재 사용자 정보 추출"""
    return await verify_token(credentials)


@router.post("", response_model=VideoAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_video_asset(
    content_id: int,
    asset_data: VideoAssetCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """영상 파일 정보 생성"""
    # 컨텐츠 존재 확인
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # content_id 일치 확인
    if asset_data.content_id != content_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content ID mismatch"
        )
    
    db_asset = VideoAsset(
        content_id=asset_data.content_id,
        video_url=asset_data.video_url,
        duration=asset_data.duration,
        resolution=asset_data.resolution
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.get("", response_model=List[VideoAssetResponse])
async def list_video_assets(
    content_id: int,
    db: Session = Depends(get_db)
):
    """컨텐츠의 영상 파일 정보 목록 조회"""
    assets = db.query(VideoAsset).filter(VideoAsset.content_id == content_id).all()
    return assets


@router.get("/{asset_id}", response_model=VideoAssetResponse)
async def get_video_asset(
    content_id: int,
    asset_id: int,
    db: Session = Depends(get_db)
):
    """영상 파일 정보 상세 조회"""
    asset = db.query(VideoAsset).filter(
        VideoAsset.id == asset_id,
        VideoAsset.content_id == content_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video asset not found"
        )
    
    return asset


@router.put("/{asset_id}", response_model=VideoAssetResponse)
async def update_video_asset(
    content_id: int,
    asset_id: int,
    asset_data: VideoAssetUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """영상 파일 정보 수정"""
    asset = db.query(VideoAsset).filter(
        VideoAsset.id == asset_id,
        VideoAsset.content_id == content_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video asset not found"
        )
    
    if asset_data.video_url is not None:
        asset.video_url = asset_data.video_url
    if asset_data.duration is not None:
        asset.duration = asset_data.duration
    if asset_data.resolution is not None:
        asset.resolution = asset_data.resolution
    
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video_asset(
    content_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """영상 파일 정보 삭제"""
    asset = db.query(VideoAsset).filter(
        VideoAsset.id == asset_id,
        VideoAsset.content_id == content_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video asset not found"
        )
    
    db.delete(asset)
    db.commit()
    return None
