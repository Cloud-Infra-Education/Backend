"""
VideoAsset model
영상 파일 정보 테이블
"""
from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class VideoAsset(Base):
    """영상 파일 정보 모델"""
    __tablename__ = "video_assets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    video_url = Column(String(500), nullable=False)
    duration = Column(Float, nullable=True)  # 초 단위
    resolution = Column(String(20), nullable=True)  # 예: "1080p", "720p", "4K"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    content = relationship("Content", back_populates="video_assets")
    
    def __repr__(self):
        return f"<VideoAsset(id={self.id}, content_id={self.content_id}, video_url={self.video_url})>"
