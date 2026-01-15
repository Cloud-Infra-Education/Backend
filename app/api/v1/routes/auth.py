"""
Authentication API endpoints
로그인, 로그아웃, 회원가입
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import httpx
from app.core.database import get_db
from app.core.security import security
from app.core.config import settings
from app.services.auth import auth_service
from app.services.user_service import user_service
from app.schemas.user import UserCreate, UserLogin
from app.schemas.auth import TokenResponse, RegisterResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입
    
    Args:
        user_data: 회원가입 정보 (이메일, 비밀번호, 지역코드, 구독상태)
        db: 데이터베이스 세션
    
    Returns:
        회원가입 성공 메시지 및 사용자 정보
    """
    try:
        user = await user_service.create_user(db, user_data)
        return RegisterResponse(
            message="User registered successfully",
            user_id=user.id,
            email=user.email
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # DB 연결 오류 감지
        if "timeout" in error_msg.lower() or "connection" in error_msg.lower() or "connect" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connection failed: {error_msg}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {error_msg}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    로그인
    
    Args:
        credentials: 로그인 정보 (이메일, 비밀번호)
        db: 데이터베이스 세션
    
    Returns:
        JWT 액세스 토큰
    """
    # 데이터베이스에서 사용자 조회 (타임아웃 처리)
    try:
        user = user_service.get_user_by_email(db, credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # 비밀번호 검증
        if not user_service.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
    except HTTPException:
        raise
    except Exception as e:
        # DB 연결 오류 등 기타 예외 처리
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
    
    # Keycloak에서 토큰 발급
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{auth_service.keycloak_url}/realms/{auth_service.realm}/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": auth_service.client_id or "backend-client",
                    "username": credentials.email,
                    "password": credentials.password,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get token from Keycloak"
                )
            
            token_data = response.json()
            return TokenResponse(
                access_token=token_data["access_token"],
                token_type="bearer",
                expires_in=token_data.get("expires_in", 3600)
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    로그아웃
    
    Args:
        credentials: JWT 토큰
    
    Returns:
        로그아웃 성공 메시지
    
    Note:
        Keycloak의 경우 토큰을 무효화하려면 refresh token이 필요합니다.
        현재는 클라이언트에서 토큰을 삭제하는 방식으로 처리합니다.
    """
    # Keycloak에서 토큰 무효화 시도 (refresh token이 있는 경우)
    # 현재 구현에서는 클라이언트에서 토큰 삭제를 권장
    return {
        "message": "Logged out successfully. Please delete the token on client side."
    }
