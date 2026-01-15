"""
Authentication API endpoints
로그인, 로그아웃, 회원가입
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import httpx
import os
import subprocess
import json
from typing import Optional
from app.core.database import get_db
from app.core.security import security
from app.core.config import settings
from app.services.auth import auth_service
from app.services.user_service import user_service
from app.schemas.user import UserCreate, UserLogin
from app.schemas.auth import TokenResponse, RegisterResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


async def create_keycloak_user(
    email: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> bool:
    """
    Keycloak에 사용자를 생성합니다.
    
    Args:
        email: 사용자 이메일
        password: 사용자 비밀번호
        first_name: 이름 (선택)
        last_name: 성 (선택)
    
    Returns:
        bool: 성공 여부
    """
    try:
        realm = os.getenv("KEYCLOAK_REALM", "formation-lap")
        keycloak_url = os.getenv("KEYCLOAK_URL", "https://api.exampleott.click/keycloak")
        admin_username = os.getenv("KEYCLOAK_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")
        
        # 1. Admin 토큰 획득
        token_cmd = [
            "curl", "-k", "-s", "-X", "POST",
            f"{keycloak_url}/realms/master/protocol/openid-connect/token",
            "-d", f"client_id=admin-cli",
            "-d", f"username={admin_username}",
            "-d", f"password={admin_password}",
            "-d", "grant_type=password"
        ]
        
        token_result = subprocess.run(
            token_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if token_result.returncode != 0:
            print(f"Keycloak Admin token failed: {token_result.stderr}")
            return False
        
        token_data = json.loads(token_result.stdout)
        admin_token = token_data.get("access_token")
        if not admin_token:
            print("No admin token in response")
            return False
        
        # 2. 사용자 생성
        user_data = {
            "email": email,
            "username": email,
            "enabled": True,
            "emailVerified": True,
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False
            }],
            "requiredActions": []
        }
        
        if first_name:
            user_data["firstName"] = first_name
        if last_name:
            user_data["lastName"] = last_name
        
        create_cmd = [
            "curl", "-k", "-s", "-w", "\n%{http_code}",
            "-X", "POST",
            f"{keycloak_url}/admin/realms/{realm}/users",
            "-H", f"Authorization: Bearer {admin_token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(user_data)
        ]
        
        create_result = subprocess.run(
            create_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # HTTP 상태 코드 추출
        output_lines = create_result.stdout.strip().split("\n")
        http_code = int(output_lines[-1]) if output_lines and output_lines[-1].isdigit() else 0
        
        if http_code in [201, 409]:  # 201: 생성됨, 409: 이미 존재
            print(f"Keycloak user created successfully: {email}")
            return True
        else:
            print(f"Keycloak user creation failed: HTTP {http_code}")
            if create_result.stdout:
                print(f"Response: {create_result.stdout[:200]}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"Keycloak JSON decode error: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("Keycloak user creation timeout")
        return False
    except Exception as e:
        print(f"Keycloak user creation error: {type(e).__name__}: {e}")
        return False


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
        # 1. 데이터베이스에 사용자 생성
        user = await user_service.create_user(db, user_data)
        
        # 2. Keycloak에도 사용자 생성
        try:
            await create_keycloak_user(
                email=user.email,
                password=user_data.password,
                first_name=user_data.first_name,
                last_name=user_data.last_name
            )
        except Exception as kc_error:
            # Keycloak 생성 실패해도 DB에는 저장되었으므로 경고만 출력
            print(f"Warning: Keycloak user creation failed: {kc_error}")
        
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
                # Keycloak에 사용자가 없을 수 있으므로 생성 시도
                try:
                    keycloak_created = await create_keycloak_user(
                        email=credentials.email,
                        password=credentials.password,
                        first_name=None,
                        last_name=None
                    )
                    if keycloak_created:
                        # 사용자 생성 후 다시 토큰 발급 시도
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
                        if response.status_code == 200:
                            token_data = response.json()
                            return TokenResponse(
                                access_token=token_data["access_token"],
                                token_type="bearer",
                                expires_in=token_data.get("expires_in", 3600)
                            )
                except Exception as create_error:
                    print(f"Keycloak auto-creation during login failed: {create_error}")
                
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
