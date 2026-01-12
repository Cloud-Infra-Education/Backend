# Backend/users/database.py
import aiomysql
import os
import asyncio
from dotenv import load_dotenv

# .env 파일로부터 환경 변수를 읽어옵니다.
load_dotenv()

# 환경 변수 매핑 (아까 확인한 .env의 변수명과 일치시켰습니다)
DB_HOST = os.getenv("DB_HOST")      # kor-writer... 주소가 들어옵니다.
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")  # .env의 DB_PASSWORD와 매칭
DB_NAME = os.getenv("DB_NAME")      # my_app

async def get_db_conn(retries: int = 5, delay: int = 3):
    """
    DB 연결 함수 - 환경 변수가 정상적으로 로드되었는지 확인 후 연결을 시도합니다.
    """
    if not DB_HOST:
        raise ValueError("[ERROR] DB_HOST 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            # DEBUG 로그 추가: 어떤 정보로 접속을 시도하는지 출력
            if attempt == 1:
                print(f"\n[DEBUG] DB 접속 시도 중... Host: {DB_HOST}, User: {DB_USER}, DB: {DB_NAME}")

            conn = await aiomysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                db=DB_NAME,
                autocommit=True,
                connect_timeout=5,
            )
            print(f"✅ DB 연결 성공! ({DB_HOST})")
            return conn
        except Exception as e:
            last_error = e
            print(f"❌ DB 연결 실패 ({attempt}/{retries}): {e}")
            await asyncio.sleep(delay)

    # 최종 실패 시 에러 발생
    raise RuntimeError(f"DB 연결 최종 실패: {last_error}")


async def init_db():
    """
    초기 테이블 생성 함수
    """
    conn = await get_db_conn()
    try:
        async with conn.cursor() as cur:
            # users 테이블 생성
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    last_region VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # videos 테이블 생성
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    video_id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    file_path VARCHAR(255),
                    view_count INT DEFAULT 0
                )
            """)

        print("✅ RDS 테이블 초기화 완료 (users, videos)")
    finally:
        conn.close()
