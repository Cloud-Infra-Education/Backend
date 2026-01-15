"""
FastAPI Backend Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.routes import health, users, auth, contents, content_likes, watch_history, video_assets, search

import os

# root_path는 환경 변수에서 읽거나 기본값 사용
root_path = os.getenv("ROOT_PATH", "")

# Ingress를 통해 /api prefix가 붙는 경우를 대비하여 root_path 설정
# /docs로 접근해도 /api/openapi.json을 찾을 수 있도록 설정
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",  # Swagger UI 활성화
    redoc_url="/redoc",  # ReDoc 활성화
    openapi_url="/openapi.json",  # root_path가 /api이므로 /openapi.json만 지정
    root_path=root_path if root_path else None  # Ingress의 /api prefix를 위해
)

# /api/docs와 /docs 경로 모두 제공 (Ingress의 /api prefix를 위해)
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

@app.get("/api/docs", response_class=HTMLResponse)
async def custom_swagger_ui_html():
    """root_path가 /api이므로 /openapi.json만 지정하면 실제로는 /api/openapi.json이 됨"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",  # root_path가 /api이므로 실제로는 /api/openapi.json이 됨
        title=app.title + " - Swagger UI"
    )

@app.get("/docs", response_class=HTMLResponse)
async def root_swagger_ui_html():
    """루트 /docs 경로도 /api/openapi.json을 참조하도록 설정
    root_path="/api"가 설정되어 있으므로 /openapi.json만 지정하면 됨"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",  # root_path가 /api이므로 실제로는 /api/openapi.json이 됨
        title=app.title + " - Swagger UI"
    )

@app.get("/api/openapi.json")
async def get_openapi_endpoint():
    return get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes
    )

# 데이터베이스 테이블 생성 (개발용)
# 프로덕션에서는 Alembic 마이그레이션 사용
# 연결 실패 시에도 애플리케이션은 시작되도록 예외 처리
@app.on_event("startup")
async def startup_event():
    import asyncio
    try:
        # 데이터베이스 연결을 별도 스레드에서 실행하여 블로킹 방지
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: Base.metadata.create_all(bind=engine))
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
app.include_router(search.router, prefix="/api/v1", tags=["Search"])


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
