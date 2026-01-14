"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Database URL 구성
if settings.DATABASE_URL:
    database_url = settings.DATABASE_URL
elif all([settings.DB_HOST, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME]):
    database_url = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}?charset=utf8mb4"
else:
    # 기본값 (로컬 개발용 SQLite)
    # 컨테이너 내부에서는 /tmp 디렉토리 사용
    import os
    db_path = os.getenv("DB_PATH", "/tmp/test.db")
    database_url = f"sqlite:///{db_path}"

# SQLAlchemy 엔진 생성
if database_url.startswith("sqlite"):
    # SQLite는 pool_pre_ping과 pool_recycle을 지원하지 않음
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # SQLite는 단일 스레드만 허용
        echo=settings.DEBUG
    )
else:
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # 연결 유효성 검사
        pool_recycle=3600,   # 1시간마다 연결 재사용
        echo=settings.DEBUG  # 디버그 모드에서 SQL 쿼리 출력
    )

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모델이 상속받을 클래스)
Base = declarative_base()


def get_db():
    """
    데이터베이스 세션 의존성
    FastAPI의 Depends에서 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
