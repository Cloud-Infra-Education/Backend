"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Backend API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Optional[str] = None
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Keycloak (인증 서버)
    KEYCLOAK_URL: Optional[str] = None
    KEYCLOAK_REALM: Optional[str] = None
    KEYCLOAK_CLIENT_ID: Optional[str] = None
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None
    
    # Keycloak Admin API (관리자 API 접근용)
    KEYCLOAK_ADMIN_USERNAME: Optional[str] = None
    KEYCLOAK_ADMIN_PASSWORD: Optional[str] = None
    
    # JWT
    JWT_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY: Optional[str] = None
    
    # Meilisearch (검색 서버)
    MEILISEARCH_URL: Optional[str] = None
    MEILISEARCH_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: int = 3306
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    
    # S3 & CloudFront
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: str = "ap-northeast-2"
    CLOUDFRONT_DOMAIN: Optional[str] = None  # 예: www.exampleott.click
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # .env 파일의 추가 필드 무시


settings = Settings()
