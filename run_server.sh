#!/bin/bash
# Backend/run_server.sh
# 로컬 개발 서버 실행 스크립트

echo "=== FastAPI 서버 시작 ==="
echo "서버 주소: http://localhost:8000"
echo "API 문서: http://localhost:8000/docs"
echo "ReDoc 문서: http://localhost:8000/redoc"
echo ""
echo "사용 가능한 엔드포인트:"
echo "  - GET /search/search?q=검색어&limit=10&offset=0  (검색 API)"
echo "  - GET /search/health  (헬스 체크)"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo "========================="
echo ""

cd "$(dirname "$0")"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
