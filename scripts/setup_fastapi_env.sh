#!/bin/bash
# FastAPI INTERNAL_TOKEN 환경 변수 설정 스크립트

set -e

INTERNAL_TOKEN="${INTERNAL_TOKEN:-formation-lap-internal-token-2024-secret-key}"
NAMESPACE="${NAMESPACE:-formation-lap}"

echo "=========================================="
echo "FastAPI INTERNAL_TOKEN 설정"
echo "=========================================="
echo "Namespace: $NAMESPACE"
echo "Token: $INTERNAL_TOKEN"
echo ""

# Kubernetes Secret 생성/업데이트
echo "Kubernetes Secret 생성 중..."
kubectl create secret generic fastapi-internal-token \
  --from-literal=INTERNAL_TOKEN="$INTERNAL_TOKEN" \
  -n "$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "✅ Secret 생성 완료!"
echo ""
echo "Deployment에 환경 변수 추가 방법:"
echo "  env:"
echo "    - name: INTERNAL_TOKEN"
echo "      valueFrom:"
echo "        secretKeyRef:"
echo "          name: fastapi-internal-token"
echo "          key: INTERNAL_TOKEN"
echo ""
