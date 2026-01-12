# EKS 클러스터 배포 가이드

## 📋 현재 준비된 것들

### ✅ 완료된 작업
1. **Kubernetes 매니페스트 파일 준비**
   - Deployment: `Manifests/base/deployment/user-deployment.yaml`
   - Service: `Manifests/base/services/user-service.yaml`
   - ConfigMap: `Manifests/base/configmap/db-config.yaml` (DB 연결 정보)
   - Secret: `Manifests/base/secret/db-secret.yaml` (DB 비밀번호)
   - Namespace: `formation-lap`

2. **환경 변수 설정**
   - RDS Proxy 엔드포인트 설정 완료
   - ConfigMap과 Secret으로 분리 관리

3. **배포 스크립트**
   - `deploy-to-eks.sh`: 자동 배포 스크립트

## 🚀 배포 방법

### 전제 조건
1. AWS CLI 설정 완료
2. kubectl 설치 및 EKS 클러스터 연결
3. Docker 이미지가 ECR에 푸시되어 있어야 함

### 1단계: EKS 클러스터 연결

```bash
# EKS 클러스터 이름 확인
aws eks list-clusters --region ap-northeast-2

# kubectl 설정 업데이트 (클러스터 이름을 실제 이름으로 변경)
aws eks update-kubeconfig --name <cluster-name> --region ap-northeast-2

# 연결 확인
kubectl get nodes
```

### 2단계: Docker 이미지 빌드 및 푸시 (필요한 경우)

```bash
cd /root/Backend

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  404457776061.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 빌드
docker build -t y2om-user-service:latest .

# 이미지 태그
docker tag y2om-user-service:latest \
  404457776061.dkr.ecr.ap-northeast-2.amazonaws.com/y2om-user-service:v5

# 이미지 푸시
docker push 404457776061.dkr.ecr.ap-northeast-2.amazonaws.com/y2om-user-service:v5
```

### 3단계: Deployment 매니페스트 업데이트 (이미지 태그 변경 시)

```bash
# user-deployment.yaml에서 이미지 태그를 새 버전으로 변경
# 예: v4 -> v5
```

### 4단계: 배포 실행

```bash
cd /root/Backend
./deploy-to-eks.sh
```

또는 수동으로:

```bash
cd /root/Manifests/base

# Namespace 생성
kubectl create namespace formation-lap --dry-run=client -o yaml | kubectl apply -f -

# ConfigMap/Secret 적용
kubectl apply -f configmap/db-config.yaml
kubectl apply -f secret/db-secret.yaml

# Deployment 적용
kubectl apply -f deployment/user-deployment.yaml

# Service 적용
kubectl apply -f services/user-service.yaml
```

## 🔍 배포 확인

### Pod 상태 확인
```bash
kubectl get pods -n formation-lap -l app=ott-users
```

### Pod 로그 확인
```bash
# 실시간 로그
kubectl logs -n formation-lap -l app=ott-users -f

# 특정 Pod 로그
POD_NAME=$(kubectl get pods -n formation-lap -l app=ott-users -o jsonpath='{.items[0].metadata.name}')
kubectl logs -n formation-lap $POD_NAME
```

### Service 확인
```bash
kubectl get svc -n formation-lap user-service
```

### 포트 포워딩으로 로컬 테스트
```bash
kubectl port-forward -n formation-lap svc/user-service 8000:8000
```

그 다음 브라우저에서:
```
http://localhost:8000/docs
```

## 🧪 API 테스트

### Pod 내부에서 테스트
```bash
# Pod에 접속
kubectl exec -it -n formation-lap $(kubectl get pods -n formation-lap -l app=ott-users -o jsonpath='{.items[0].metadata.name}') -- bash

# Pod 내부에서 API 테스트
curl -X POST "http://localhost:8000/users/users/register" \
  -H "Content-Type: application/json" \
  -H "x-region: seoul" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

### 포트 포워딩을 통한 테스트
```bash
# 포트 포워딩 실행 (다른 터미널에서)
kubectl port-forward -n formation-lap svc/user-service 8000:8000

# 로컬에서 테스트
curl -X POST "http://localhost:8000/users/users/register" \
  -H "Content-Type: application/json" \
  -H "x-region: seoul" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

## 🔧 환경 변수 업데이트

### ConfigMap 업데이트 (비밀 정보 제외)
```bash
# ConfigMap 편집
kubectl edit configmap db-config -n formation-lap

# 또는 파일 수정 후 적용
kubectl apply -f Manifests/base/configmap/db-config.yaml
kubectl rollout restart deployment/ott-users -n formation-lap
```

### Secret 업데이트 (비밀 정보)
```bash
# Secret 편집
kubectl edit secret db-secret -n formation-lap

# 또는 파일 수정 후 적용
kubectl apply -f Manifests/base/secret/db-secret.yaml
kubectl rollout restart deployment/ott-users -n formation-lap
```

## ❌ 문제 해결

### Pod가 시작되지 않는 경우
```bash
# Pod 상태 확인
kubectl describe pod -n formation-lap -l app=ott-users

# 이벤트 확인
kubectl get events -n formation-lap --sort-by='.lastTimestamp'
```

### DB 연결 실패
- Pod 로그 확인: `kubectl logs -n formation-lap -l app=ott-users`
- ConfigMap/Secret 확인: `kubectl get configmap db-config -n formation-lap -o yaml`
- RDS Proxy 보안 그룹이 EKS Worker 보안 그룹을 허용하는지 확인

### 이미지 Pull 실패
- ECR 권한 확인
- 이미지 태그 확인
- ECR 로그인 상태 확인

## 📝 참고사항

- RDS Proxy 엔드포인트가 변경되면 ConfigMap을 업데이트하고 Deployment를 재시작해야 합니다
- DB 비밀번호는 Secret으로 관리하므로 주의해서 다루세요
- 프로덕션 환경에서는 더 강화된 보안 설정을 고려하세요
