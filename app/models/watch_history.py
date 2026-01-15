"""
WatchHistory model
시청기록 테이블
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class WatchHistory(Base):
    """시청기록 모델"""
    __tablename__ = "watch_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    last_played_time = Column(Float, default=0.0, nullable=False)  # 초 단위
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="watch_histories")
    content = relationship("Content", back_populates="watch_histories")
    
    def __repr__(self):
        return f"<WatchHistory(id={self.id}, user_id={self.user_id}, content_id={self.content_id}, last_played_time={self.last_played_time})>"
