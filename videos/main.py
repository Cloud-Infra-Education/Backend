# Backend/videos/main.py
from fastapi import APIRouter, HTTPException, Query
from users.database import get_db_conn # 기존 DB 연결 함수 재사용

router = APIRouter(prefix="/videos")

# 1. 영상 검색: /videos/search?q={문자}
@router.get("/search")
async def search_video(q: str = Query(..., min_length=1)):
    conn = get_db_conn()
    cur = conn.cursor()
    # 제목에 검색어가 포함된 영상 찾기
    cur.execute("SELECT * FROM videos WHERE title LIKE ?", (f'%{q}%',))
    results = cur.fetchall()
    conn.close()
    
    if not results:
        return {"message": "검색 결과가 없습니다.", "results": []}
    
    return {"results": [{"id": r[0], "title": r[1], "desc": r[2]} for r in results]}

# 2. 영상 업로드 (정보 등록): /videos/upload/{video_id}
# 경로에서 {video_id}를 빼고, 알아서 생성되게 바꿉니다.
@router.post("/upload")
async def upload_video_info(title: str, description: str):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        # video_id를 명시하지 않으면 DB가 알아서 번호를 매겨요!
        cur.execute("INSERT INTO videos (title, description) VALUES (?, ?)",
                    (title, description))
        new_id = cur.lastrowid # 방금 만들어진 번호가 몇 번인지 가져옵니다.
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return {"message": "등록 완료!", "video_id": new_id}
# 3. 영상 시청 (조회수 증가): /videos/watch/{video_id}
@router.get("/watch/{video_id}")
async def watch_video(video_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    
    # 영상 확인 및 조회수 1 증가
    cur.execute("UPDATE videos SET view_count = view_count + 1 WHERE video_id = ?", (video_id,))
    cur.execute("SELECT title, file_path FROM videos WHERE video_id = ?", (video_id,))
    video = cur.fetchone()
    conn.commit()
    conn.close()
    
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다.")
    
    return {"title": video[0], "url": video[1], "status": "Streaming started"}
