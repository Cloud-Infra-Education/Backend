# Backend/users/main.py
from fastapi import Header, Request, HTTPException, APIRouter
from pydantic import BaseModel
from users.database import get_db_conn

# 1. 'app = FastAPI()' 대신 'router'를 생성합니다.
router = APIRouter(prefix="/users")

# 데이터를 받을 양식
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

# 2. @app.post를 @router.post로 바꿉니다. (prefix가 /users이므로 경로는 /login만 써도 됩니다)
@router.post("/login")
async def login(item: LoginRequest, request: Request, x_region: str = Header(None)):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        sql = "SELECT user_id FROM users WHERE email=? AND password=?"
        cur.execute(sql, (item.email, item.password))
        user = cur.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")

        user_id = user[0]
        region = x_region or "Unknown"
        ip = request.client.host

        cur.execute("UPDATE users SET last_region=? WHERE user_id=?", (region, user_id))
        cur.execute("INSERT INTO access_logs (user_id, region, ip_address) VALUES (?, ?, ?)",
                    (user_id, region, ip))

        conn.commit()
        return {"message": "로그인 성공!", "user_id": user_id, "region": region}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"로그인 처리 에러: {str(e)}")
    finally:
        conn.close()

@router.post("/logout")
async def logout():
    return {"message": "로그아웃 되었습니다. 다음에 또 오세요!"}
@router.post("/register")
async def register(item: RegisterRequest, x_region: str = Header(None)):
    # 1. 다시 await를 붙여서 연결을 가져옵니다.
    conn = await get_db_conn()
    try:
        # 2. 비동기 커서 사용
        async with conn.cursor() as cur:
            # 3. ? 대신 %s 사용
            await cur.execute("SELECT email FROM users WHERE email=%s", (item.email,))
            if await cur.fetchone():
                raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

            sql = "INSERT INTO users (email, password, last_region) VALUES (%s, %s, %s)"
            await cur.execute(sql, (item.email, item.password, x_region or "Unknown"))
            # autocommit=True이므로 별도의 commit()은 생략 가능합니다.
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 에러: {str(e)}")
    finally:
        conn.close()
    return {"message": "회원가입 완료! (RDS Proxy 연결됨)"}
