"""
JWT verification utilities
Keycloak에서 발급한 JWT 토큰 검증만 담당
"""
from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.core.config import settings
from app.services.auth import auth_service


security = HTTPBearer(
    scheme_name="Bearer",
    description="JWT 토큰을 입력하세요. Keycloak에서 발급받은 토큰을 사용합니다."
)

# 공개 키 캐시
_cached_public_key: Optional[str] = None


async def _get_public_key() -> str:
    """
    Keycloak에서 공개 키를 가져옵니다 (캐시 사용)
    
    Returns:
        PEM 형식의 공개 키
    """
    global _cached_public_key
    
    # 캐시된 키가 있으면 사용
    if _cached_public_key:
        return _cached_public_key
    
    # .env에 설정된 키가 있고 유효하면 사용 (선택사항)
    if settings.JWT_PUBLIC_KEY and settings.JWT_PUBLIC_KEY.strip():
        # .env의 키가 올바른 형식인지 확인
        if "BEGIN PUBLIC KEY" in settings.JWT_PUBLIC_KEY:
            _cached_public_key = settings.JWT_PUBLIC_KEY.replace('\\n', '\n')
            return _cached_public_key
    
    # Keycloak에서 동적으로 가져오기 (기본 방법)
    try:
        public_key = await auth_service.get_public_key()
        if public_key:
            _cached_public_key = public_key
            return public_key
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch public key from Keycloak: {str(e)}"
        )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="JWT public key not available. Please ensure Keycloak is accessible."
    )


async def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    JWT 토큰 검증
    Keycloak에서 발급한 토큰의 유효성을 검증합니다.
    
    Args:
        credentials: HTTP Bearer 토큰
        
    Returns:
        디코딩된 토큰 페이로드
        
    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    token = credentials.credentials
    
    # 공개 키 가져오기
    public_key = await _get_public_key()
    
    try:
        # JWT 토큰 검증
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_exp": True}
        )
        return payload
    except JWTError as e:
        # 서명 검증 실패 시 캐시 초기화하고 재시도
        global _cached_public_key
        if "Signature verification failed" in str(e):
            _cached_public_key = None
            try:
                public_key = await _get_public_key()
                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_signature": True, "verify_exp": True}
                )
                return payload
            except JWTError:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> dict:
    """
    현재 사용자 정보 추출
    JWT 토큰에서 사용자 정보를 추출합니다.
    
    Args:
        credentials: HTTP Bearer 토큰
        
    Returns:
        사용자 정보 딕셔너리
    """
    # verify_token은 async이므로 의존성 주입에서 사용
    pass
