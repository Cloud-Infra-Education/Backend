from fastapi import FastAPI, HTTPException, Body
import uuid
import os
import sys
from pathlib import Path

# 우리가 만든 공통 모듈 경로 연결
sys.path.append(str(Path(__file__).parent.parent))
from common.database import get_db_connection
from common.logger import get_request_info
app = FastAPI(title="OTT User Service")

# 1. 헬스체크 (서버 상태 확인용)
@app.get("/")
def health_check():
    return {"status": "ok", "service": "users"}

# 2. 회원가입 API
@app.post("/signup")
def signup(username: str = Body(...), password: str = Body(...), name: str = Body(...)):
    trace_id = str(uuid.uuid4())[:8]
    region = os.getenv("REGION_NAME", "seoul")
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed")
    
    try:
        with conn.cursor() as cursor:
            # 유저 생성 쿼리 (실제 운영 시 비밀번호 해싱 필수!)
            sql = "INSERT INTO users (username, password, name, region) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (username, password, name, region))
        return {"trace_id": trace_id, "region": region, "message": "회원가입 성공!"}
    finally:
        conn.close()

# 3. 로그인 API (리전 정보 확인 포함)
@app.post("/login")
def login(username: str = Body(...), password: str = Body(...)):
    trace_id = str(uuid.uuid4())[:8]
    region = os.getenv("REGION_NAME", "seoul")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM users WHERE username = %s AND password = %s"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
            
            if user:
                print(f"[LOGIN SUCCESS] TRACE:{trace_id} | REGION:{region} | User:{username}")
                return {
                    "trace_id": trace_id,
                    "region": region,
                    "message": f"{user['name']}님 환영합니다!",
                    "user_info": {"id": user['username'], "name": user['name']}
                }
            else:
                raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀립니다.")
    finally:
        conn.close()
