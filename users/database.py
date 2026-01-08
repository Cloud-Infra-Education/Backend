# Backend/users/database.py
import aiomysql
import os
import asyncio

# 환경 변수
DB_HOST = os.getenv("RDS_PROXY_SEOUL")   # RDS Proxy endpoint
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME", "ott_db")


async def get_db_conn(retries: int = 5, delay: int = 3):
    """
    RDS Proxy 초기 지연을 고려한 DB 연결 함수
    """
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            conn = await aiomysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                db=DB_NAME,
                autocommit=True,
                connect_timeout=5,
            )
            return conn
        except Exception as e:
            last_error = e
            print(f"❌ DB 연결 실패 ({attempt}/{retries}): {e}")
            await asyncio.sleep(delay)

    # 여기까지 오면 진짜 실패
    raise RuntimeError(f"DB 연결 최종 실패: {last_error}")


async def init_db():
    """
    ⚠️ 운영 환경에서는 직접 호출하지 않는 것을 권장
    - 로컬 개발
    - 초기 1회 세팅
    - Job / Migration 용도로만 사용
    """
    conn = await get_db_conn()
    try:
        async with conn.cursor() as cur:
            # users 테이블
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    last_region VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # videos 테이블
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    video_id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    file_path VARCHAR(255),
                    view_count INT DEFAULT 0
                )
            """)

        print("✅ RDS 테이블 초기화 완료")
    finally:
        conn.close()

