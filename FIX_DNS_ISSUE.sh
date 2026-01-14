#!/bin/bash
# DNS 문제 해결: Lambda 환경 변수를 내부 Kubernetes 서비스 엔드포인트로 변경

set -e

FUNCTION_NAME="formation-lap-video-processor"
REGION="ap-northeast-2"

# Kubernetes 서비스 정보
SERVICE_NAME="video-service"
NAMESPACE="formation-lap"
SERVICE_PORT="8000"

# 내부 엔드포인트 구성
INTERNAL_ENDPOINT="http://${SERVICE_NAME}.${NAMESPACE}.svc.cluster.local:${SERVICE_PORT}/api"

echo "=========================================="
echo "Lambda 환경 변수 업데이트"
echo "=========================================="
echo "함수명: $FUNCTION_NAME"
echo "내부 엔드포인트: $INTERNAL_ENDPOINT"
echo ""

# 현재 환경 변수 가져오기
CURRENT_ENV=$(aws lambda get-function-configuration \
  --function-name $FUNCTION_NAME \
  --region $REGION \
  --query 'Environment.Variables' \
  --output json)

echo "현재 환경 변수:"
echo "$CURRENT_ENV" | jq .
echo ""

# 환경 변수 업데이트
echo "환경 변수 업데이트 중..."
aws lambda update-function-configuration \
  --function-name $FUNCTION_NAME \
  --region $REGION \
  --environment "Variables={
    CATALOG_API_BASE=$INTERNAL_ENDPOINT,
    INTERNAL_TOKEN=formation-lap-internal-token-2024-secret-key,
    DB_HOST=formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com,
    DB_USER=admin,
    DB_PASSWORD=test1234,
    DB_NAME=ott_db
  }" \
  --output json > /tmp/lambda_update.json

echo ""
echo "✅ 업데이트 완료!"
echo ""
echo "업데이트된 환경 변수:"
cat /tmp/lambda_update.json | jq '.Environment.Variables'

echo ""
echo "=========================================="
echo "다음 단계:"
echo "1. S3에 테스트 비디오 업로드"
echo "2. CloudWatch 로그 확인"
echo "3. DB에서 contents 테이블 확인"
echo "=========================================="
