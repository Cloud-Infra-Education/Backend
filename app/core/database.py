"""
Database connection and session management
"""
from sqlalchemy import create_engine, text
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
    # RDS Proxy는 TLS 연결이 필수이므로 SSL 파라미터 추가
    connect_args = {
        "connect_timeout": 3,  # 연결 타임아웃 3초로 단축
    }
    # RDS Proxy는 항상 TLS 연결이 필요하므로 SSL 파라미터 추가
    # pymysql에서 SSL을 활성화하려면 ssl 딕셔너리를 전달해야 함
    # check_hostname=False로 설정하면 호스트명 검증을 건너뜀
    connect_args["ssl"] = {
        "check_hostname": False
    }
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # 연결 유효성 검사
        pool_recycle=3600,   # 1시간마다 연결 재사용
        connect_args=connect_args,
        pool_timeout=3,  # 풀 타임아웃 3초로 단축
        pool_reset_on_return='commit',  # 연결 반환 시 리셋
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
        # 연결 테스트 (빠른 실패) - SQLAlchemy 2.0에서는 text() 필요
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            # 연결 실패 시에도 세션을 제공 (일부 기능이 동작할 수 있음)
            # 실제 쿼리 실행 시 오류가 발생할 것이므로 여기서는 예외를 무시
            pass
        yield db
    finally:
        db.close()
