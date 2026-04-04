"""
Video Service API endpoints
비디오 검색 및 시청 정보 조회
"""
import os
import pymysql
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/videos", tags=["Videos"])

# DB 연결 정보 (환경 변수에서 가져오기)
# 백엔드 API의 환경 변수와 동일하게 사용
# DATABASE_URL 형식: mysql+pymysql://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "y2om_db")  # 기본값을 y2om_db로 변경

# DATABASE_URL에서 파싱 (백엔드 API와 동일한 방식)
if DATABASE_URL and not DB_HOST:
    try:
        # mysql+pymysql://user:password@host:port/dbname 형식 파싱
        import re
        match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
        if match:
            DB_USER = match.group(1)
            DB_PASSWORD = match.group(2)
            DB_HOST = match.group(3)
            DB_NAME = match.group(5)
    except:
        pass

# S3 버킷 정보
S3_BUCKET = os.getenv("S3_BUCKET_NAME", os.getenv("S3_BUCKET", "y2om-my-origin-bucket-087730891580"))
S3_REGION = os.getenv("S3_REGION", "ap-northeast-2")

def get_db_connection():
    """RDS Proxy에 연결"""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"DB 연결 실패: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@router.get("/search/")
def search_videos(q: Optional[str] = Query(None, description="검색어")):
    """영상 검색"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if q:
                # 제목이나 설명에서 검색
                search_pattern = f"%{q}%"
                cursor.execute(
                    """
                    SELECT c.id, c.title, c.description, c.age_rating, c.like_count,
                           va.video_url, va.thumbnail_url, va.duration
                    FROM contents c
                    LEFT JOIN video_assets va ON c.id = va.content_id
                    WHERE c.title LIKE %s OR c.description LIKE %s
                    ORDER BY c.like_count DESC
                    """,
                    (search_pattern, search_pattern)
                )
            else:
                # 검색어가 없으면 전체 목록
                cursor.execute(
                    """
                    SELECT c.id, c.title, c.description, c.age_rating, c.like_count,
                           va.video_url, va.thumbnail_url, va.duration
                    FROM contents c
                    LEFT JOIN video_assets va ON c.id = va.content_id
                    ORDER BY c.like_count DESC
                    """
                )
            
            videos = cursor.fetchall()
            
            # S3 URL 생성
            for video in videos:
                if video.get('video_url'):
                    # 이미 전체 URL이면 그대로 사용, 아니면 S3 URL 생성
                    if not video['video_url'].startswith('http'):
                        # s3:// 형식이면 변환
                        if video['video_url'].startswith('s3://'):
                            video['video_url'] = video['video_url'].replace('s3://', f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/')
                        else:
                            video['video_url'] = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{video['video_url']}"
                
                if video.get('thumbnail_url'):
                    # 썸네일 URL도 S3 URL로 변환
                    if not video['thumbnail_url'].startswith('http'):
                        if video['thumbnail_url'].startswith('s3://'):
                            video['thumbnail_url'] = video['thumbnail_url'].replace('s3://', f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/')
                        else:
                            video['thumbnail_url'] = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{video['thumbnail_url']}"
            
            return {
                "query": q,
                "count": len(videos),
                "videos": videos
            }
    except Exception as e:
        logger.error(f"영상 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/watch/{video_id}")
def watch_video(video_id: int):
    """영상 시청 정보 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 영상 정보 조회
            cursor.execute(
                """
                SELECT c.id, c.title, c.description, c.age_rating, c.like_count,
                       va.video_url, va.thumbnail_url, va.duration
                FROM contents c
                LEFT JOIN video_assets va ON c.id = va.content_id
                WHERE c.id = %s
                """,
                (video_id,)
            )
            video = cursor.fetchone()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            # S3 URL 생성
            if video.get('video_url') and not video['video_url'].startswith('http'):
                if video['video_url'].startswith('s3://'):
                    video['video_url'] = video['video_url'].replace('s3://', f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/')
                else:
                    video['video_url'] = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{video['video_url']}"
            
            if video.get('thumbnail_url') and not video['thumbnail_url'].startswith('http'):
                if video['thumbnail_url'].startswith('s3://'):
                    video['thumbnail_url'] = video['thumbnail_url'].replace('s3://', f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/')
                else:
                    video['thumbnail_url'] = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{video['thumbnail_url']}"
            
            return {
                "video": video
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"영상 시청 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
