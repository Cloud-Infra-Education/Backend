# Backend/main.py (최상위 main)
import logging
from fastapi import FastAPI
from users.main import router as user_router
from videos.main import router as video_router
from app.search.main import router as search_router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI(
    title="Global Search API",
    description="RDS Proxy를 통한 글로벌 검색/조회 API",
    version="1.0.0"
)

# 라우터 연결
app.include_router(user_router, prefix="/users")
app.include_router(video_router, prefix="/videos")
app.include_router(search_router, prefix="/search", tags=["search"])

# 루트 경로 추가
@app.get("/")
async def root():
    """
    API 루트 엔드포인트
    """
    return {
        "message": "Global Search API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "search": "/search/search?q=검색어&limit=10&offset=0",
            "health": "/search/health"
        }
    }

# Backend/main.py
from users.database import init_db
import asyncio

# 개발 모드에서만 실행
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("FastAPI 서버 시작")
    print("=" * 50)
    print("서버 주소: http://localhost:8000")
    print("API 문서: http://localhost:8000/docs")
    print("ReDoc 문서: http://localhost:8000/redoc")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)