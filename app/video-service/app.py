import os
import pymysql
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = FastAPI()

# DB 연결 정보 (환경 변수에서 가져오기)
DB_HOST = os.getenv("DB_HOST", "formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "test1234")
DB_NAME = os.getenv("DB_NAME", "ott_db")

# S3 버킷 정보
S3_BUCKET = os.getenv("S3_BUCKET", "yuh-team-formation-lap-origin-s3")
S3_REGION = os.getenv("S3_REGION", "ap-northeast-2")

# 내부 토큰 (Lambda와 공유)
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "formation-lap-internal-token-2024-secret-key")

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

@app.get("/")
def root():
    return {"ok": True, "service": "video-service"}

@app.get("/videos/search/")
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
                        video['video_url'] = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{video['video_url']}"
                
                if video.get('thumbnail_url'):
                    # 썸네일 URL도 S3 URL로 변환
                    if not video['thumbnail_url'].startswith('http'):
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

@app.get("/videos/watch/{video_id}")
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
                video['video_url'] = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{video['video_url']}"
            
            if video.get('thumbnail_url') and not video['thumbnail_url'].startswith('http'):
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

# ============= 내부 Upsert API (Lambda에서 호출) =============

def verify_internal_token(x_internal_token: str = Header(None)):
    """내부 토큰 검증 (Lambda와 공유 시크릿)"""
    if not INTERNAL_TOKEN:
        raise HTTPException(status_code=500, detail="INTERNAL_TOKEN not configured")
    if not x_internal_token or x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid internal token")

@app.put("/api/v1/contents/{content_id}/upsert-internal", dependencies=[Depends(verify_internal_token)])
def upsert_content_internal(content_id: int, payload: dict):
    """
    Lambda에서 호출하는 내부용 contents upsert 엔드포인트
    payload: {"title": "...", "description": "...", "age_rating": "..."}
    """
    title = payload.get("title")
    description = payload.get("description", "")
    age_rating = payload.get("age_rating", "ALL")
    
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 기존 content 확인
            cursor.execute(
                "SELECT id FROM contents WHERE id = %s",
                (content_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 기존 content 업데이트
                cursor.execute(
                    """
                    UPDATE contents 
                    SET title = %s, description = %s, age_rating = %s
                    WHERE id = %s
                    """,
                    (title, description, age_rating, content_id)
                )
            else:
                # 새 content 생성
                cursor.execute(
                    """
                    INSERT INTO contents (id, title, description, age_rating, like_count)
                    VALUES (%s, %s, %s, %s, 0)
                    """,
                    (content_id, title, description, age_rating)
                )
            
            conn.commit()
            
            return {
                "id": content_id,
                "title": title,
                "age_rating": age_rating
            }
    except Exception as e:
        logger.error(f"Contents upsert 실패: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
