"""
FastAPI Backend Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.routes import health, users, auth, contents, content_likes, watch_history, video_assets

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# 데이터베이스 테이블 생성 (개발용)
# 프로덕션에서는 Alembic 마이그레이션 사용
# 연결 실패 시에도 애플리케이션은 시작되도록 예외 처리
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️  Database connection failed during startup: {str(e)}")
        print("   Application will continue, but database features may not work.")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(contents.router, prefix="/api/v1", tags=["Contents"])
app.include_router(content_likes.router, prefix="/api/v1", tags=["Content Likes"])
app.include_router(watch_history.router, prefix="/api/v1", tags=["Watch History"])
app.include_router(video_assets.router, prefix="/api/v1", tags=["Video Assets"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Backend API",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
