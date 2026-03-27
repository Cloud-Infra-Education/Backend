#!/bin/bash
# FastAPI 내부 upsert 엔드포인트 테스트 스크립트 (로컬용)

set -e

# 환경 변수 설정 (로컬 테스트용 기본값)
API_BASE="${API_BASE:-http://localhost:8000/api}"
INTERNAL_TOKEN="${INTERNAL_TOKEN:-formation-lap-internal-token-2024-secret-key}"
CONTENT_ID="${1:-1}"

echo "=========================================="
echo "FastAPI 내부 Upsert API 테스트 (로컬)"
echo "=========================================="
echo "API Base: $API_BASE"
echo "Content ID: $CONTENT_ID"
echo ""

# 테스트 데이터
PAYLOAD=$(cat <<EOF
{
  "title": "Test Video",
  "description": "Uploaded video: test_video",
  "age_rating": "ALL"
}
EOF
)

echo "요청 보내는 중..."
echo "URL: $API_BASE/v1/contents/$CONTENT_ID/upsert-internal"
echo "Payload: $PAYLOAD"
echo ""

# API 호출
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X PUT "$API_BASE/v1/contents/$CONTENT_ID/upsert-internal" \
  -H "X-Internal-Token: $INTERNAL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" 2>&1)

# HTTP 코드 추출
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

echo "=========================================="
echo "응답 결과"
echo "=========================================="
echo "HTTP Status: $HTTP_CODE"
echo "Response Body:"
echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ 성공! DB에 반영되었는지 확인하세요:"
  echo "   SELECT * FROM contents WHERE id=$CONTENT_ID;"
  exit 0
else
  echo "❌ 실패 (HTTP $HTTP_CODE)"
  if [ -z "$HTTP_CODE" ]; then
    echo ""
    echo "⚠️  FastAPI 서버가 실행 중인지 확인하세요:"
    echo "   curl http://localhost:8000/api/v1/health"
  fi
  exit 1
fi
