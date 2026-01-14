"""
ContentLike model
좋아요 상세 테이블
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ContentLike(Base):
    """컨텐츠 좋아요 모델"""
    __tablename__ = "contents_likes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contents_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="content_likes")
    content = relationship("Content", back_populates="content_likes")
    
    # Unique constraint: 한 사용자는 한 컨텐츠에 한 번만 좋아요 가능
    # SQLite는 제약조건 이름을 지원하지 않을 수 있으므로 조건부로 설정
    __table_args__ = (
        UniqueConstraint('user_id', 'contents_id', name='unique_user_content_like'),
    ) if __name__ != "__main__" else ()
    
    def __repr__(self):
        return f"<ContentLike(id={self.id}, user_id={self.user_id}, contents_id={self.contents_id})>"
