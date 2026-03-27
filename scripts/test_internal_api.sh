#!/bin/bash
# FastAPI 내부 upsert 엔드포인트 테스트 스크립트

set -e

# 환경 변수 설정
API_BASE="${API_BASE:-https://api.matchacake.click/api}"
INTERNAL_TOKEN="${INTERNAL_TOKEN:-formation-lap-internal-token-2024-secret-key}"
CONTENT_ID="${1:-1}"

echo "=========================================="
echo "FastAPI 내부 Upsert API 테스트"
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

# API 호출 (video-service는 /api/v1/contents 경로 사용)
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X PUT "$API_BASE/v1/contents/$CONTENT_ID/upsert-internal" \
  -H "X-Internal-Token: $INTERNAL_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

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
  echo "✅ 성공!"
  exit 0
else
  echo "❌ 실패 (HTTP $HTTP_CODE)"
  exit 1
fi
