"""
Authentication schemas
"""
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RegisterResponse(BaseModel):
    """회원가입 응답 스키마"""
    message: str
    user_id: int
    email: str
