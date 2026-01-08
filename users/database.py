# Backend/users/database.py
import aiomysql
import os

# 테라폼 Output으로 확인한 환경변수들
DB_HOST = os.getenv("RDS_PROXY_SEOUL") # 서울 리전 프록시 사용
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = "ott_db" 

async def get_db_conn():
    try:
        conn = await aiomysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            autocommit=True
        )
        return conn
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        raise e

# Backend/users/database.py 에 추가
async def init_db():
    conn = await get_db_conn()
    try:
        async with conn.cursor() as cur:
            # 1. DB 선택
            await cur.execute("CREATE DATABASE IF NOT EXISTS ott_db")
            await cur.execute("USE ott_db")
            
            # 2. 유저 테이블 생성
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    last_region VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 3. 비디오 테이블 생성
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    video_id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    file_path VARCHAR(255),
                    view_count INT DEFAULT 0
                )
            """)
        print("✅ RDS 테이블 초기화 완료!")
    finally:
        conn.close()
