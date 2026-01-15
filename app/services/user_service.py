"""
User service
사용자 관련 비즈니스 로직
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from passlib.context import CryptContext
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
import httpx
from app.core.config import settings

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """사용자 서비스"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_id_from_jwt(db: Session, jwt_payload: dict) -> Optional[int]:
        """
        JWT 토큰 페이로드에서 DB user_id 가져오기
        
        JWT 토큰의 email 필드를 사용하여 DB users 테이블에서
        해당 사용자의 id를 조회합니다.
        
        Args:
            db: 데이터베이스 세션
            jwt_payload: JWT 토큰에서 디코딩된 페이로드 (verify_token의 반환값)
        
        Returns:
            DB user_id (없으면 None)
        """
        # JWT에서 email 추출
        email = jwt_payload.get("email")
        if not email:
            return None
        
        # DB에서 email로 사용자 조회
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        
        return user.id
    
    @staticmethod
    async def create_user(db: Session, user_data: UserCreate) -> User:
        """사용자 생성"""
        # 이메일 중복 확인
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Keycloak에 사용자 생성 (선택적 - 실패해도 계속 진행)
        keycloak_user_id = None
        try:
            keycloak_user_id = await UserService._create_keycloak_user(user_data)
        except Exception as e:
            # Keycloak이 없거나 접근 불가능한 경우 경고만 출력하고 계속 진행
            print(f"⚠️  Keycloak 사용자 생성 실패 (무시하고 계속 진행): {str(e)}")
        
        # 데이터베이스에 사용자 생성
        hashed_password = UserService.hash_password(user_data.password)
        db_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            region_code=user_data.region_code,
            subscription_status=user_data.subscription_status
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            # Keycloak 사용자 삭제 시도
            if keycloak_user_id:
                try:
                    await UserService._delete_keycloak_user(keycloak_user_id)
                except Exception:
                    pass  # 삭제 실패는 무시
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
    
    @staticmethod
    async def _create_keycloak_user(user_data: UserCreate) -> str:
        """Keycloak에 사용자 생성"""
        from app.services.auth import auth_service
        
        admin_token = await auth_service._get_admin_token()
        if not admin_token:
            raise ValueError("Admin token not available")
        
        url = f"{auth_service.keycloak_url}/admin/realms/{auth_service.realm}/users"
        user_payload = {
            "username": user_data.email,
            "email": user_data.email,
            "enabled": True,
            "emailVerified": True,  # 회원가입 시 이메일 인증 완료로 설정
            "credentials": [{
                "type": "password",
                "value": user_data.password,
                "temporary": False
            }]
        }
        
        # firstName과 lastName 추가 (Keycloak에서 필요)
        if user_data.first_name:
            user_payload["firstName"] = user_data.first_name
        if user_data.last_name:
            user_payload["lastName"] = user_data.last_name
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {admin_token}",
                    "Content-Type": "application/json"
                },
                json=user_payload,
                timeout=10.0
            )
            response.raise_for_status()
            # Keycloak은 Location 헤더에 사용자 ID를 반환
            location = response.headers.get("Location", "")
            if location:
                return location.split("/")[-1]
            raise ValueError("Failed to get user ID from Keycloak")
    
    @staticmethod
    async def _delete_keycloak_user(user_id: str):
        """Keycloak에서 사용자 삭제"""
        from app.services.auth import auth_service
        
        admin_token = await auth_service._get_admin_token()
        if not admin_token:
            return
        
        url = f"{auth_service.keycloak_url}/admin/realms/{auth_service.realm}/users/{user_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    url,
                    headers={"Authorization": f"Bearer {admin_token}"},
                    timeout=10.0
                )
                response.raise_for_status()
            except Exception:
                pass  # 삭제 실패는 무시
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
        """사용자 정보 수정"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user_data.email and user_data.email != user.email:
            # 이메일 중복 확인
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = user_data.email
        
        if user_data.region_code is not None:
            user.region_code = user_data.region_code
        
        if user_data.subscription_status is not None:
            user.subscription_status = user_data.subscription_status
        
        db.commit()
        db.refresh(user)
        return user


user_service = UserService()
