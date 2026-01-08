from fastapi import FastAPI, Query, HTTPException
import uuid
import os
import sys
from pathlib import Path

# 공통 모듈 경로 연결
sys.path.append(str(Path(__file__).parent.parent))
from common.database import get_db_connection

app = FastAPI(title="OTT Content Service")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "content"}

# 1. 글로벌 영상 검색 API
@app.get("/search")
def search_videos(q: str = Query(None, min_length=1)):
    trace_id = str(uuid.uuid4())[:8]
    region = os.getenv("REGION_NAME", "seoul")
    
    print(f"[SEARCH] TRACE:{trace_id} | REGION:{region} | Query:{q}")
    
    conn = get_db_connection()
    if not conn:
        return {"trace_id": trace_id, "region": region, "error": "DB 연결 실패"}

    try:
        with conn.cursor() as cursor:
            # 리전별로 최적화된 콘텐츠를 검색하는 쿼리 (예시)
            sql = "SELECT * FROM contents WHERE title LIKE %s AND (target_region = %s OR target_region = 'global')"
            cursor.execute(sql, (f"%{q}%", region))
            results = cursor.fetchall()
            
        return {
            "trace_id": trace_id,
            "region": region,
            "results": results,
            "count": len(results)
        }
    finally:
        conn.close()

# 2. 영상 상세 조회 API
@app.get("/videos/{video_id}")
def get_video_detail(video_id: int):
    trace_id = str(uuid.uuid4())[:8]
    region = os.getenv("REGION_NAME", "seoul")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM contents WHERE id = %s"
            cursor.execute(sql, (video_id,))
            video = cursor.fetchone()
            
            if not video:
                raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다.")
                
            return {"trace_id": trace_id, "region": region, "data": video}
    finally:
        conn.close()
