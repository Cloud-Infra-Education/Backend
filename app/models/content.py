"""
Content model
컨텐츠 메인 테이블
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Content(Base):
    """컨텐츠 모델"""
    __tablename__ = "contents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    age_rating = Column(String(10), nullable=True)  # 예: "ALL", "12", "15", "18"
    like_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    content_likes = relationship("ContentLike", back_populates="content", cascade="all, delete-orphan")
    watch_histories = relationship("WatchHistory", back_populates="content", cascade="all, delete-orphan")
    video_assets = relationship("VideoAsset", back_populates="content", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Content(id={self.id}, title={self.title})>"
