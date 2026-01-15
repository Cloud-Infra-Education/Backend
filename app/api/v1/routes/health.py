"""
Health check endpoints
"""
from fastapi import APIRouter


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check():
    """레디니스 체크 엔드포인트"""
    return {"status": "ready"}
