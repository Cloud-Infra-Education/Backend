#!/bin/bash
# Terraform outputs에서 RDS Proxy 엔드포인트를 가져와서 .env 파일을 업데이트하는 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/../Terraform/03-database"
ENV_FILE="${SCRIPT_DIR}/.env"

echo "🔍 Terraform state에서 RDS Proxy 엔드포인트를 확인 중..."

# Terraform outputs를 먼저 시도 (더 깔끔함)
if cd "$TERRAFORM_DIR" && terraform output -json kor_db_proxy_endpoint > /dev/null 2>&1; then
    KOR_ENDPOINT=$(cd "$TERRAFORM_DIR" && terraform output -raw kor_db_proxy_endpoint 2>/dev/null)
else
    # outputs가 없으면 state show로 직접 추출
    echo "⚠️  Terraform outputs가 활성화되지 않았습니다. terraform state show를 사용합니다."
    KOR_ENDPOINT=$(cd "$TERRAFORM_DIR" && terraform state show 'module.database.aws_db_proxy.kor' 2>/dev/null | grep -E '^\s+endpoint\s*=' | sed 's/.*= "\(.*\)"/\1/')
fi

if [ -z "$KOR_ENDPOINT" ]; then
    echo "❌ RDS Proxy 엔드포인트를 찾을 수 없습니다."
    exit 1
fi

echo "✅ Korea RDS Proxy 엔드포인트: $KOR_ENDPOINT"

# .env 파일 백업
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
    echo "📦 .env 파일 백업 완료"
fi

# .env 파일 업데이트
if [ -f "$ENV_FILE" ]; then
    # DB_HOST가 있으면 업데이트, 없으면 추가
    if grep -q "^DB_HOST=" "$ENV_FILE"; then
        # macOS와 Linux 모두 지원
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^DB_HOST=.*|DB_HOST=$KOR_ENDPOINT|" "$ENV_FILE"
        else
            sed -i "s|^DB_HOST=.*|DB_HOST=$KOR_ENDPOINT|" "$ENV_FILE"
        fi
        echo "✅ .env 파일의 DB_HOST가 업데이트되었습니다."
    else
        # DB_HOST가 없으면 파일 시작 부분에 추가
        echo "DB_HOST=$KOR_ENDPOINT" >> "$ENV_FILE"
        echo "✅ .env 파일에 DB_HOST가 추가되었습니다."
    fi
else
    # .env 파일이 없으면 생성
    cat > "$ENV_FILE" << EOF
DB_HOST=$KOR_ENDPOINT
DB_USER=admin
DB_PASSWORD=StrongPassword123!
DB_NAME=my_app

# 리전 정보
REGION_NAME=ap-northeast-2
EOF
    echo "✅ .env 파일이 생성되었습니다."
fi

echo ""
echo "📝 업데이트된 .env 파일 내용:"
grep "^DB_HOST=" "$ENV_FILE"

echo ""
echo "✨ 완료! 서버를 재시작하거나 환경 변수를 다시 로드하세요."
