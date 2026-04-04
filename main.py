"""
FastAPI Backend Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1.routes import health, users, auth, contents, content_likes, watch_history, video_assets, videos, contents_internal, video_assets_internal, search

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
app.include_router(contents_internal.router, prefix="/api/v1", tags=["Contents Internal"])
app.include_router(video_assets_internal.router, prefix="/api/v1", tags=["Video Assets Internal"])
app.include_router(video_assets.router, prefix="/api/v1", tags=["Video Assets"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(videos.router, tags=["Videos"])  # /videos prefix는 라우터에 이미 있음


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Backend API",
        "version": settings.APP_VERSION
    }


# Keycloak 프록시 엔드포인트
from fastapi import Request, HTTPException
from fastapi.responses import Response
import httpx

@app.api_route("/keycloak/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def keycloak_proxy(request: Request, path: str):
    """Keycloak 요청을 실제 Keycloak 서비스로 프록시"""
    try:
        # Keycloak 서비스 URL (Kubernetes 내부 서비스)
        keycloak_url = "http://keycloak-service.formation-lap.svc.cluster.local:8080"
        target_url = f"{keycloak_url}/{path}"
        
        # 쿼리 파라미터 포함
        if request.url.query:
            target_url += f"?{request.url.query}"
        
        # 요청 헤더 복사 (Host 헤더 제외)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # 요청 본문 읽기
        body = await request.body()
        
        # Keycloak으로 요청 프록시
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body
            )
        
        # 응답 헤더 복사 (일부 제외)
        response_headers = dict(response.headers)
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        for header in excluded_headers:
            response_headers.pop(header, None)
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get("content-type")
        )
        
    except httpx.RequestError as e:
        # Keycloak 서비스에 연결할 수 없는 경우
        return Response(
            content=f"Keycloak service unavailable: {str(e)}",
            status_code=503,
            media_type="text/plain"
        )
    except Exception as e:
        # 기타 오류
        return Response(
            content=f"Proxy error: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
