#!/bin/bash
echo "=== API 서버 상태 체크 ==="
echo ""

echo "1. 서버 프로세스:"
ps aux | grep -E "uvicorn.*8001" | grep -v grep && echo "✅ 실행 중" || echo "❌ 실행 중이 아님"

echo ""
echo "2. 서버 응답:"
curl -s http://localhost:8001/ > /dev/null 2>&1 && echo "✅ 서버 응답 정상" || echo "❌ 서버 응답 없음"

echo ""
echo "3. DB 연결 테스트:"
cd /root/Backend
python3 -c "
import asyncio
from users.database import get_db_conn

async def test():
    try:
        conn = await get_db_conn()
        print('✅ DB 연결 성공!')
        conn.close()
    except Exception as e:
        print(f'❌ DB 연결 실패: {type(e).__name__}')

asyncio.run(test())
" 2>&1 | tail -1

echo ""
echo "4. 환경 변수:"
cd /root/Backend
cat .env | grep DB_HOST | head -1

echo ""
echo "=== 체크 완료 ==="
