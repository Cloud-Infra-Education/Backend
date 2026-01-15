"""
Keycloak integration service
인증은 Keycloak에서 처리하며, 이 서비스는 Keycloak과의 연동만 담당합니다.
"""
from typing import Optional, Dict, Any, List
import httpx
from app.core.config import settings


class AuthService:
    """Keycloak 인증 서비스"""
    
    def __init__(self):
        # localhost를 127.0.0.1로 변환 (DNS 해석 문제 방지)
        keycloak_url = settings.KEYCLOAK_URL or ""
        if keycloak_url:
            keycloak_url = keycloak_url.replace("localhost", "127.0.0.1")
        
        self.keycloak_url = keycloak_url
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self.admin_username = settings.KEYCLOAK_ADMIN_USERNAME
        self.admin_password = settings.KEYCLOAK_ADMIN_PASSWORD
        self._admin_token: Optional[str] = None
    
    def get_public_key_url(self) -> Optional[str]:
        """
        Keycloak 공개키 URL 반환
        JWT 검증을 위한 공개키를 가져올 수 있는 URL을 반환합니다.
        
        Returns:
            공개키 URL
        """
        if not all([self.keycloak_url, self.realm]):
            return None
        
        return f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"
    
    async def _get_admin_token(self) -> Optional[str]:
        """
        Keycloak 관리자 토큰 발급
        Admin API를 사용하기 위한 관리자 토큰을 발급받습니다.
        
        Returns:
            관리자 액세스 토큰
        """
        if not all([self.keycloak_url, self.admin_username, self.admin_password]):
            return None
        
        if self._admin_token:
            return self._admin_token
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.keycloak_url}/realms/master/protocol/openid-connect/token",
                    data={
                        "grant_type": "password",
                        "client_id": "admin-cli",
                        "username": self.admin_username,
                        "password": self.admin_password,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                response.raise_for_status()
                token_data = response.json()
                self._admin_token = token_data.get("access_token")
                return self._admin_token
        except Exception as e:
            print(f"Failed to get admin token: {str(e)}")
            return None
    
    async def list_users(
        self,
        first: int = 0,
        max_results: int = 100,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        사용자 목록 조회
        Keycloak Admin API를 통해 사용자 목록을 가져옵니다.
        
        Args:
            first: 시작 인덱스
            max_results: 최대 결과 수
            search: 검색어 (사용자명, 이메일 등)
            
        Returns:
            사용자 목록
        """
        admin_token = await self._get_admin_token()
        if not admin_token:
            raise ValueError("Admin token not available. Please configure KEYCLOAK_ADMIN_USERNAME and KEYCLOAK_ADMIN_PASSWORD.")
        
        if not all([self.keycloak_url, self.realm]):
            raise ValueError("Keycloak URL and Realm must be configured.")
        
        url = f"{self.keycloak_url}/admin/realms/{self.realm}/users"
        params = {
            "first": first,
            "max": max_results
        }
        
        if search:
            params["search"] = search
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {admin_token}",
                        "Content-Type": "application/json"
                    },
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # 토큰 만료 시 재발급
                self._admin_token = None
                return await self.list_users(first, max_results, search)
            raise ValueError(f"Failed to list users: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to list users: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        사용자 ID로 사용자 정보 조회
        Keycloak Admin API를 통해 특정 사용자 정보를 가져옵니다.
        
        Args:
            user_id: Keycloak 사용자 ID
            
        Returns:
            사용자 정보 딕셔너리
        """
        admin_token = await self._get_admin_token()
        if not admin_token:
            raise ValueError("Admin token not available. Please configure KEYCLOAK_ADMIN_USERNAME and KEYCLOAK_ADMIN_PASSWORD.")
        
        if not all([self.keycloak_url, self.realm]):
            raise ValueError("Keycloak URL and Realm must be configured.")
        
        url = f"{self.keycloak_url}/admin/realms/{self.realm}/users/{user_id}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {admin_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # 토큰 만료 시 재발급
                self._admin_token = None
                return await self.get_user_by_id(user_id)
            elif e.response.status_code == 404:
                return None
            raise ValueError(f"Failed to get user: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to get user: {str(e)}")
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        사용자 정보 조회 (JWT 토큰 기반)
        Keycloak UserInfo 엔드포인트를 통해 사용자 정보를 가져옵니다.
        
        Args:
            access_token: Keycloak 액세스 토큰
            
        Returns:
            사용자 정보 딕셔너리
        """
        if not all([self.keycloak_url, self.realm]):
            return None
        
        url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/userinfo"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Failed to get user info: {str(e)}")
            return None
    
    async def get_public_key(self, kid: Optional[str] = None) -> Optional[str]:
        """
        Keycloak에서 JWT 검증용 공개 키를 가져옵니다.
        
        Args:
            kid: Key ID (JWT 헤더에서 추출). None이면 서명용 키 중 첫 번째 사용
        
        Returns:
            PEM 형식의 공개 키
        """
        if not all([self.keycloak_url, self.realm]):
            return None
        
        try:
            url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    timeout=10.0
                )
                response.raise_for_status()
                certs = response.json()
                
                # kid가 제공된 경우 해당 키를 찾고, 없으면 서명용 키 중 첫 번째 사용
                key = None
                if kid:
                    for k in certs['keys']:
                        if k.get('kid') == kid and k.get('use') == 'sig':
                            key = k
                            break
                
                # kid가 없거나 찾지 못한 경우 서명용 키 중 첫 번째 사용
                if not key:
                    for k in certs['keys']:
                        if k.get('use') == 'sig':
                            key = k
                            break
                
                # 여전히 키를 찾지 못한 경우 첫 번째 키 사용 (하위 호환성)
                if not key:
                    key = certs['keys'][0]
                
                # JWK to PEM 변환
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import rsa
                import base64
                
                n_bytes = base64.urlsafe_b64decode(key['n'] + '==')
                e_bytes = base64.urlsafe_b64decode(key['e'] + '==')
                
                n = int.from_bytes(n_bytes, 'big')
                e = int.from_bytes(e_bytes, 'big')
                
                pub_key = rsa.RSAPublicNumbers(e, n).public_key()
                pem = pub_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()
                return pem
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Failed to get public key from Keycloak: {e.response.text}")
        except Exception as e:
            raise ValueError(f"Error getting public key: {str(e)}")


# 전역 인증 서비스 인스턴스
auth_service = AuthService()
