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


async def _get_public_key(kid: Optional[str] = None) -> str:
    """
    Keycloak에서 공개 키를 가져옵니다 (캐시 사용)
    
    Args:
        kid: Key ID (JWT 헤더에서 추출)
    
    Returns:
        PEM 형식의 공개 키
    """
    global _cached_public_key
    
    # kid가 제공된 경우 캐시를 사용하지 않고 항상 최신 키 가져오기
    # (Keycloak이 키를 로테이션할 수 있으므로)
    if not kid:
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
        public_key = await auth_service.get_public_key(kid)
        if public_key:
            if not kid:
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
    
    # JWT 헤더에서 kid 추출
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
    except Exception:
        kid = None
    
    # 공개 키 가져오기 (kid 사용)
    public_key = await _get_public_key(kid)
    
    # Issuer 확인
    expected_issuer = f"{auth_service.keycloak_url}/realms/{auth_service.realm}"
    
    try:
        # JWT 토큰 검증 (audience 검증 비활성화 - Keycloak의 account audience 사용)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_exp": True, "verify_iss": True, "verify_aud": False},
            issuer=expected_issuer
        )
        return payload
    except JWTError as e:
        # 서명 검증 실패 시 캐시 초기화하고 재시도 (다른 kid로)
        global _cached_public_key
        if "Signature verification failed" in str(e) or "Invalid issuer" in str(e):
            _cached_public_key = None
            try:
                # kid 없이 다시 시도 (서명용 키 자동 선택)
                public_key = await _get_public_key(None)
                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_signature": True, "verify_exp": True, "verify_iss": True, "verify_aud": False},
                    issuer=expected_issuer
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
