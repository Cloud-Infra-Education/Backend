# Kubernetes 환경 Keycloak 설정 가이드

로컬 환경과 Kubernetes 환경의 차이점과 설정 방법을 안내합니다.

## 환경별 차이점

### 로컬 환경 (Docker Compose)
- Keycloak: `http://localhost:8080`
- Backend API: `http://localhost:8000`
- DB: Keycloak 내장 H2 (dev-file)
- 설정: `.env` 파일 사용

### Kubernetes 환경
- Keycloak: Kubernetes Service를 통해 접근
- Backend API: Kubernetes Service를 통해 접근
- DB: 외부 데이터베이스 (PostgreSQL 등) 또는 영구 볼륨
- 설정: ConfigMap, Secret 사용

## Kubernetes 환경 설정 단계

### 1. Keycloak 배포

Keycloak을 Kubernetes에 배포합니다:

```yaml
# keycloak-deployment.yaml 예시
apiVersion: apps/v1
kind: Deployment
metadata:
  name: keycloak
  namespace: formation-lap
spec:
  replicas: 1
  selector:
    matchLabels:
      app: keycloak
  template:
    metadata:
      labels:
        app: keycloak
    spec:
      containers:
      - name: keycloak
        image: quay.io/keycloak/keycloak:latest
        args: ["start-dev"]
        env:
        - name: KEYCLOAK_ADMIN
          value: "admin"
        - name: KEYCLOAK_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: keycloak-admin-secret
              key: password
        ports:
        - containerPort: 8080
```

### 2. Keycloak Service 생성

```yaml
apiVersion: v1
kind: Service
metadata:
  name: keycloak
  namespace: formation-lap
spec:
  selector:
    app: keycloak
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

### 3. Backend API 환경 변수 설정 (ConfigMap/Secret)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: formation-lap
data:
  KEYCLOAK_URL: "http://keycloak:8080"
  KEYCLOAK_REALM: "my-realm"
  KEYCLOAK_CLIENT_ID: "backend-client"
  KEYCLOAK_ADMIN_USERNAME: "admin"
---
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
  namespace: formation-lap
type: Opaque
stringData:
  KEYCLOAK_ADMIN_PASSWORD: "admin"
  JWT_PUBLIC_KEY: |
    -----BEGIN PUBLIC KEY-----
    ...
    -----END PUBLIC KEY-----
```

### 4. 포트포워딩으로 접근

로컬에서 Kubernetes의 Keycloak에 접근하려면:

```bash
# Keycloak 포트포워딩
kubectl port-forward svc/keycloak 8080:8080 -n formation-lap

# Backend API 포트포워딩
kubectl port-forward svc/backend-service 8000:8000 -n formation-lap
```

### 5. Keycloak 설정 (Kubernetes 환경)

포트포워딩 후 로컬과 동일하게 설정:

1. http://localhost:8080 접속 (포트포워딩 후)
2. master realm에 admin 사용자 생성
3. my-realm 생성
4. backend-client 생성
5. 테스트 사용자 생성

## 환경 변수 설정 스크립트

Kubernetes 환경에서 JWT Public Key를 가져오는 스크립트:

```bash
#!/bin/bash
# get-jwt-public-key.sh

KEYCLOAK_URL=${KEYCLOAK_URL:-"http://localhost:8080"}
REALM=${KEYCLOAK_REALM:-"my-realm"}

# Keycloak에서 Public Key 가져오기
python3 << EOF
import json
import base64
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

response = requests.get("${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/certs")
certs = response.json()
key = certs['keys'][0]

n = int.from_bytes(base64.urlsafe_b64decode(key['n'] + '=='), 'big')
e = int.from_bytes(base64.urlsafe_b64decode(key['e'] + '=='), 'big')

pub_key = rsa.RSAPublicNumbers(e, n).public_key()
pem = pub_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

print(pem)
EOF
```

## 주의사항

1. **데이터베이스**: Kubernetes 환경에서는 영구 볼륨이나 외부 DB를 사용해야 합니다
2. **비밀번호 관리**: Secret을 사용하여 민감한 정보 관리
3. **네트워크**: Service 이름으로 접근 (`http://keycloak:8080`)
4. **환경 변수**: ConfigMap과 Secret으로 분리 관리

## 테스트 방법

### 1. 포트포워딩 후 로컬처럼 테스트

```bash
# 포트포워딩
kubectl port-forward svc/keycloak 8080:8080 -n formation-lap &
kubectl port-forward svc/backend-service 8000:8000 -n formation-lap &

# 테스트
curl http://localhost:8000/api/v1/health
```

### 2. Pod 내부에서 테스트

```bash
# Backend API Pod에 접속
kubectl exec -it <backend-pod-name> -n formation-lap -- bash

# Pod 내부에서 Keycloak 접근
curl http://keycloak:8080/health/ready
```

## 문제 해결

### Keycloak에 접근할 수 없는 경우

1. Service가 생성되었는지 확인:
```bash
kubectl get svc -n formation-lap | grep keycloak
```

2. Pod가 실행 중인지 확인:
```bash
kubectl get pods -n formation-lap | grep keycloak
```

3. 로그 확인:
```bash
kubectl logs <keycloak-pod-name> -n formation-lap
```

### 환경 변수가 적용되지 않는 경우

1. ConfigMap 확인:
```bash
kubectl get configmap backend-config -n formation-lap -o yaml
```

2. Secret 확인:
```bash
kubectl get secret backend-secrets -n formation-lap -o yaml
```

3. Pod 재시작:
```bash
kubectl rollout restart deployment/backend -n formation-lap
```
