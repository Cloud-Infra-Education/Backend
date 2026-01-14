"""
User model
사용자 정보 테이블
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class SubscriptionStatus(str, enum.Enum):
    """구독 상태"""
    FREE = "free"
    PREMIUM = "premium"
    VIP = "vip"


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    region_code = Column(String(10), nullable=True)  # 예: "KR", "US"
    subscription_status = Column(
        Enum(SubscriptionStatus),
        default=SubscriptionStatus.FREE,
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    content_likes = relationship("ContentLike", back_populates="user", cascade="all, delete-orphan")
    watch_histories = relationship("WatchHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
