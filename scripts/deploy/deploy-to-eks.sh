#!/bin/bash
# EKS 클러스터에 Backend 서비스를 배포하는 스크립트

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="${SCRIPT_DIR}/../Manifests/base"
NAMESPACE="formation-lap"

echo "🚀 EKS 클러스터에 Backend 서비스 배포 시작..."
echo ""

# 1. Kubernetes 클러스터 연결 확인
echo "1️⃣  Kubernetes 클러스터 연결 확인..."
if ! kubectl cluster-info > /dev/null 2>&1; then
    echo "❌ Kubernetes 클러스터에 연결할 수 없습니다."
    echo "   EKS 클러스터에 연결하려면 다음 명령어를 실행하세요:"
    echo "   aws eks update-kubeconfig --name <cluster-name> --region ap-northeast-2"
    exit 1
fi
echo "✅ 클러스터 연결 확인 완료"
echo ""

# 2. Namespace 확인/생성
echo "2️⃣  Namespace 확인/생성..."
kubectl get namespace "$NAMESPACE" > /dev/null 2>&1 || kubectl create namespace "$NAMESPACE"
echo "✅ Namespace 확인 완료"
echo ""

# 3. ConfigMap/Secret 적용
echo "3️⃣  ConfigMap/Secret 적용..."
cd "$MANIFESTS_DIR"
kubectl apply -f configmap/db-config.yaml
kubectl apply -f secret/db-secret.yaml
echo "✅ ConfigMap/Secret 적용 완료"
echo ""

# 4. Deployment 적용
echo "4️⃣  Deployment 적용..."
kubectl apply -f deployment/user-deployment.yaml
echo "✅ Deployment 적용 완료"
echo ""

# 5. Service 확인
echo "5️⃣  Service 확인..."
kubectl apply -f services/user-service.yaml
echo "✅ Service 확인 완료"
echo ""

# 6. 배포 상태 확인
echo "6️⃣  배포 상태 확인..."
echo "Pod 상태:"
kubectl get pods -n "$NAMESPACE" -l app=ott-users
echo ""
echo "Service 상태:"
kubectl get svc -n "$NAMESPACE" user-service
echo ""

# 7. Pod 로그 확인 (최근 20줄)
echo "7️⃣  Pod 로그 (최근 20줄):"
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app=ott-users -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$POD_NAME" ]; then
    kubectl logs -n "$NAMESPACE" "$POD_NAME" --tail=20
else
    echo "⚠️  Pod가 아직 생성되지 않았습니다. 잠시 후 다시 확인하세요."
fi
echo ""

echo "✨ 배포 완료!"
echo ""
echo "📝 유용한 명령어:"
echo "   # Pod 상태 확인:"
echo "   kubectl get pods -n $NAMESPACE -l app=ott-users"
echo ""
echo "   # Pod 로그 확인:"
echo "   kubectl logs -n $NAMESPACE -l app=ott-users -f"
echo ""
echo "   # 서비스 확인:"
echo "   kubectl get svc -n $NAMESPACE user-service"
echo ""
echo "   # 포트 포워딩 (로컬 테스트용):"
echo "   kubectl port-forward -n $NAMESPACE svc/user-service 8000:8000"
