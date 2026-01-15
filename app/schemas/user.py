"""
User schemas (Pydantic models)
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import SubscriptionStatus


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr
    region_code: Optional[str] = None
    subscription_status: SubscriptionStatus = SubscriptionStatus.FREE


class UserCreate(UserBase):
    """회원가입용 스키마"""
    password: str = Field(..., min_length=8, description="비밀번호 (최소 8자)")
    first_name: Optional[str] = Field(None, description="이름")
    last_name: Optional[str] = Field(None, description="성")


class UserUpdate(BaseModel):
    """사용자 정보 수정용 스키마"""
    email: Optional[EmailStr] = None
    region_code: Optional[str] = None
    subscription_status: Optional[SubscriptionStatus] = None


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """로그인용 스키마"""
    email: EmailStr
    password: str
