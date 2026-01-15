#!/bin/bash

# Backend 서버 실행 스크립트

set -e

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 환경 변수 파일 로드
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 서버 실행
echo "Starting Backend server..."
echo "Host: ${HOST:-0.0.0.0}"
echo "Port: ${PORT:-8000}"

python3 -m uvicorn main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --reload
