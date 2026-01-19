#!/bin/bash
# EKS ConfigMap의 Keycloak 설정 수정 스크립트

set -e

echo "=== Keycloak ConfigMap 수정 ==="
echo ""

# 1. 현재 ConfigMap 확인
echo "1. 현재 ConfigMap 확인..."
kubectl get configmap backend-config -n formation-lap -o yaml | grep -E "KEYCLOAK" || echo "ConfigMap이 없습니다"

echo ""
echo "2. ConfigMap 업데이트..."

# ConfigMap 패치 (KEYCLOAK 관련 설정만 업데이트)
kubectl patch configmap backend-config -n formation-lap --type merge -p '{
  "data": {
    "KEYCLOAK_URL": "https://api.exampleott.click/keycloak",
    "KEYCLOAK_REALM": "formation-lap",
    "KEYCLOAK_CLIENT_ID": "backend-client"
  }
}'

echo ""
echo "3. 업데이트된 ConfigMap 확인..."
kubectl get configmap backend-config -n formation-lap -o yaml | grep -E "KEYCLOAK"

echo ""
echo "4. Pod 재시작..."
kubectl rollout restart deployment/backend-api -n formation-lap 2>/dev/null || \
kubectl rollout restart deployment/user-service -n formation-lap 2>/dev/null || \
echo "Deployment 이름을 확인하세요: kubectl get deployments -n formation-lap"

echo ""
echo "5. Pod 상태 확인..."
sleep 5
kubectl get pods -n formation-lap | head -10

echo ""
echo "=== 완료! ==="
echo ""
echo "Pod가 재시작되면 새 설정이 적용됩니다."
echo "테스트: curl -X POST https://api.exampleott.click/api/v1/auth/register ..."
