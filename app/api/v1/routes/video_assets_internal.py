"""
VideoAssets Internal API endpoints
Lambda 함수에서 사용하는 내부 API (인증 토큰 사용)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.video_asset import VideoAsset
from app.models.content import Content
from app.schemas.video_asset import VideoAssetCreate, VideoAssetResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contents", tags=["Video Assets Internal"])

INTERNAL_TOKEN = "formation-lap-internal-token-2024-secret-key"  # Lambda와 공유하는 토큰


async def verify_internal_token(x_internal_token: str = Header(..., alias="X-Internal-Token")):
    """내부 토큰 검증"""
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token"
        )
    return True


@router.post("/{content_id}/video-assets-internal", response_model=VideoAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_video_asset_internal(
    content_id: int,
    asset_data: VideoAssetCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_internal_token)
):
    """
    Lambda 함수에서 사용하는 내부 video_assets 생성 엔드포인트
    """
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
    
    # 기존 video_asset 확인 (같은 content_id와 video_url이 있으면 업데이트)
    existing_asset = db.query(VideoAsset).filter(
        VideoAsset.content_id == content_id,
        VideoAsset.video_url == asset_data.video_url
    ).first()
    
    if existing_asset:
        # 업데이트
        if asset_data.duration is not None:
            existing_asset.duration = asset_data.duration
        if asset_data.thumbnail_url is not None:
            existing_asset.thumbnail_url = asset_data.thumbnail_url
        if asset_data.resolution is not None:
            existing_asset.resolution = asset_data.resolution
        # video_url은 그대로 유지
        db.commit()
        db.refresh(existing_asset)
        
        logger.info(f"VideoAsset updated: id={existing_asset.id}, content_id={content_id}, video_url={asset_data.video_url}")
        return existing_asset
    else:
        # 생성
        db_asset = VideoAsset(
            content_id=asset_data.content_id,
            video_url=asset_data.video_url,
            thumbnail_url=asset_data.thumbnail_url,
            duration=asset_data.duration,
            resolution=asset_data.resolution
        )
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)
        
        logger.info(f"VideoAsset created: id={db_asset.id}, content_id={content_id}, video_url={asset_data.video_url}")
        return db_asset
