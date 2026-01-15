"""
VideoAssets API endpoints
영상 파일 정보
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import security, verify_token
from fastapi.security import HTTPAuthorizationCredentials
from app.models.video_asset import VideoAsset
from app.models.content import Content
from app.schemas.video_asset import VideoAssetCreate, VideoAssetUpdate, VideoAssetResponse
from app.services.s3_service import s3_service

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


@router.get("/s3/list", response_model=List[dict])
async def list_s3_videos(
    content_id: int,
    prefix: Optional[str] = Query(None, description="S3 경로 prefix (예: videos/)"),
    max_keys: int = Query(1000, ge=1, le=1000, description="최대 반환 개수")
):
    """
    S3 버킷에서 영상 파일 목록 조회
    
    S3에 저장된 영상 파일 목록을 가져와서 CloudFront URL과 함께 반환합니다.
    """
    if not s3_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 서비스가 사용 불가능합니다. S3_BUCKET_NAME 환경 변수를 확인하세요."
        )
    
    # content_id를 prefix에 포함 (선택사항)
    if prefix is None:
        prefix = f"videos/content_{content_id}/"
    elif not prefix.endswith('/'):
        prefix = f"{prefix}/"
    
    files = s3_service.list_videos(prefix=prefix, max_keys=max_keys)
    
    return files


@router.get("/s3/url/{s3_key:path}", response_model=dict)
async def get_s3_video_url(
    content_id: int,
    s3_key: str
):
    """
    S3 파일의 CloudFront URL 조회
    
    S3 키를 받아서 CloudFront URL을 반환합니다.
    """
    if not s3_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 서비스가 사용 불가능합니다."
        )
    
    file_info = s3_service.get_file_info(s3_key)
    
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"S3 파일을 찾을 수 없습니다: {s3_key}"
        )
    
    return file_info
