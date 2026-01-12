# Backend/app/search/main.py
"""
글로벌 검색/조회 API
RDS Proxy를 통해 데이터를 조회하고, 사용자의 접속 리전 정보를 로그와 함께 기록합니다.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional, List, Dict, Any
import logging

from app.common.database import get_db_cursor
from app.common.logger import get_request_info

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search")
async def global_search(
    request: Request,
    q: str = Query(..., description="검색어"),
    limit: int = Query(10, ge=1, le=100, description="결과 개수 제한"),
    offset: int = Query(0, ge=0, description="페이지 오프셋")
):
    """
    글로벌 검색 API
    
    RDS Proxy를 통해 데이터를 검색하고, 접속 리전 정보를 로그에 기록합니다.
    
    Args:
        q: 검색어
        limit: 결과 개수 제한 (기본값: 10, 최대: 100)
        offset: 페이지 오프셋 (기본값: 0)
        request: FastAPI Request 객체
        
    Returns:
        검색 결과와 메타데이터
    """
    # Trace ID와 리전 정보 추출
    trace_id, region = get_request_info()
    
    # 클라이언트 정보 추출
    client_ip = request.client.host if request else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    
    # 로그 기록 (리전 정보 포함)
    logger.info(
        f"[SEARCH-API] 검색 요청 | "
        f"TraceID: {trace_id} | "
        f"Region: {region} | "
        f"Query: {q} | "
        f"ClientIP: {client_ip} | "
        f"Limit: {limit} | "
        f"Offset: {offset}"
    )
    
    try:
        # RDS Proxy를 통한 데이터 조회
        with get_db_cursor() as cursor:
            # 예제: 사용자 테이블에서 검색 (실제 테이블 구조에 맞게 수정 필요)
            search_query = """
                SELECT 
                    id,
                    name,
                    email,
                    created_at
                FROM users
                WHERE 
                    name LIKE %s OR
                    email LIKE %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            
            search_pattern = f"%{q}%"
            cursor.execute(search_query, (search_pattern, search_pattern, limit, offset))
            results = cursor.fetchall()
            
            # 전체 개수 조회
            count_query = """
                SELECT COUNT(*) as total
                FROM users
                WHERE 
                    name LIKE %s OR
                    email LIKE %s
            """
            cursor.execute(count_query, (search_pattern, search_pattern))
            total_result = cursor.fetchone()
            total = total_result.get("total", 0) if total_result else 0
            
            logger.info(
                f"[SEARCH-API] 검색 완료 | "
                f"TraceID: {trace_id} | "
                f"Region: {region} | "
                f"Results: {len(results)} | "
                f"Total: {total}"
            )
            
            return {
                "trace_id": trace_id,
                "region": region,
                "query": q,
                "results": results,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total
                },
                "meta": {
                    "client_ip": client_ip,
                    "user_agent": user_agent
                }
            }
            
    except Exception as e:
        logger.error(
            f"[SEARCH-API] 검색 실패 | "
            f"TraceID: {trace_id} | "
            f"Region: {region} | "
            f"Query: {q} | "
            f"Error: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "trace_id": trace_id,
                "region": region,
                "message": "검색 중 오류가 발생했습니다.",
                "error": str(e)
            }
        )


@router.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    데이터베이스 연결 상태와 리전 정보를 확인합니다.
    """
    trace_id, region = get_request_info()
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1 as health")
            result = cursor.fetchone()
            
            logger.info(
                f"[HEALTH-CHECK] 성공 | "
                f"TraceID: {trace_id} | "
                f"Region: {region}"
            )
            
            return {
                "status": "healthy",
                "trace_id": trace_id,
                "region": region,
                "database": "connected"
            }
            
    except Exception as e:
        logger.error(
            f"[HEALTH-CHECK] 실패 | "
            f"TraceID: {trace_id} | "
            f"Region: {region} | "
            f"Error: {str(e)}"
        )
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "trace_id": trace_id,
                "region": region,
                "database": "disconnected",
                "error": str(e)
            }
        )
