"""
User API endpoints
사용자 관련 API (JWT 검증 필요)
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import security, verify_token
from app.services.auth import auth_service


router = APIRouter(prefix="/users", tags=["Users"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    현재 사용자 정보 추출 (의존성 주입)
    JWT 토큰에서 사용자 정보를 추출합니다.
    """
    payload = await verify_token(credentials)
    return payload


@router.get("")
async def list_users(
    current_user: Dict[str, Any] = Depends(get_current_user),
    first: int = Query(0, ge=0, description="시작 인덱스"),
    max_results: int = Query(100, ge=1, le=1000, description="최대 결과 수"),
    search: Optional[str] = Query(None, description="검색어 (사용자명, 이메일 등)")
):
    """
    사용자 목록 조회 (관리자만)
    
    Args:
        first: 시작 인덱스 (기본값: 0)
        max_results: 최대 결과 수 (기본값: 100, 최대: 1000)
        search: 검색어 (선택사항)
    
    Returns:
        사용자 목록
    """
    # 관리자 권한 확인
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles and "realm-admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        users = await auth_service.list_users(
            first=first,
            max_results=max_results,
            search=search
        )
        return {
            "users": users,
            "count": len(users),
            "first": first,
            "max": max_results
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user list: {str(e)}"
        )


@router.get("/me")
async def get_my_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    현재 로그인한 사용자 정보 조회
    
    Returns:
        사용자 정보
    """
    return {
        "user_id": current_user.get("sub"),
        "username": current_user.get("preferred_username"),
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "roles": current_user.get("realm_access", {}).get("roles", []),
        "token_info": {
            "exp": current_user.get("exp"),
            "iat": current_user.get("iat"),
            "iss": current_user.get("iss")
        }
    }


@router.get("/{user_id}")
async def get_user_info(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    특정 사용자 정보 조회
    
    Args:
        user_id: 조회할 사용자 ID (Keycloak 사용자 ID 또는 "me")
        
    Returns:
        사용자 정보
    """
    # 본인 정보 조회인 경우
    if user_id == "me" or user_id == current_user.get("sub"):
        return await get_my_info(current_user)
    
    # 다른 사용자 정보 조회
    # 관리자 권한 확인
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles and "realm-admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to view other users"
        )
    
    try:
        user_info = await auth_service.get_user_by_id(user_id)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # 민감한 정보 제거 (필요시)
        return {
            "id": user_info.get("id"),
            "username": user_info.get("username"),
            "email": user_info.get("email"),
            "firstName": user_info.get("firstName"),
            "lastName": user_info.get("lastName"),
            "enabled": user_info.get("enabled"),
            "emailVerified": user_info.get("emailVerified"),
            "createdTimestamp": user_info.get("createdTimestamp"),
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user info: {str(e)}"
        )
