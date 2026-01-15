#!/bin/bash
# EC2에서 FastAPI를 로컬로 실행하는 스크립트 (비용 0원 테스트용)

set -e

echo "=========================================="
echo "FastAPI 로컬 실행 (EC2 내부 테스트용)"
echo "=========================================="
echo ""

# DB 연결 정보 (terraform.tfvars에서 확인한 값)
export DB_HOST="${DB_HOST:-formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com}"
export DB_USER="${DB_USER:-admin}"
export DB_PASSWORD="${DB_PASSWORD:-test1234}"
export DB_NAME="${DB_NAME:-ott_db}"
export DB_PORT="${DB_PORT:-3306}"

# 내부 토큰 (Lambda와 동일한 값)
export INTERNAL_TOKEN="${INTERNAL_TOKEN:-formation-lap-internal-token-2024-secret-key}"

echo "환경 변수 설정:"
echo "  DB_HOST: $DB_HOST"
echo "  DB_USER: $DB_USER"
echo "  DB_NAME: $DB_NAME"
echo "  INTERNAL_TOKEN: ${INTERNAL_TOKEN:0:20}..."
echo ""

cd /root/Backend

# Python 가상환경 확인 (선택사항)
if [ -d "venv" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
fi

# FastAPI 실행
echo "FastAPI 서버 시작 중..."
echo "접속 URL: http://0.0.0.0:8000"
echo "API Base: http://localhost:8000/api"
echo ""
echo "다른 터미널에서 다음 명령으로 테스트:"
echo "  cd /root/Backend"
echo "  export API_BASE=\"http://localhost:8000/api\""
echo "  export INTERNAL_TOKEN=\"formation-lap-internal-token-2024-secret-key\""
echo "  ./scripts/test_internal_api.sh 1"
echo ""
echo "=========================================="

cd /root/Backend/app/video-service
uvicorn app:app --host 0.0.0.0 --port 8000
