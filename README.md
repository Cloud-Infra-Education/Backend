# Backend API

FastAPI 기반 Backend 애플리케이션

## 구조

```
Backend/
├── app/
│   ├── __init__.py
│   ├── core/              # 핵심 설정 및 보안
│   │   ├── config.py      # 애플리케이션 설정
│   │   └── security.py    # JWT 검증
│   ├── api/               # API 라우터
│   │   └── v1/
│   │       └── routes/    # API 엔드포인트
│   ├── services/          # 외부 서비스 연동
│   │   ├── auth.py        # Keycloak 연동
│   │   └── search.py      # Meilisearch 연동
│   └── models/            # 데이터 모델
├── scripts/
│   └── run_server.sh      # 서버 실행 스크립트
├── main.py                # 애플리케이션 진입점
├── requirements.txt       # Python 의존성
├── Dockerfile             # Docker 이미지 빌드
├── docker-compose.yml     # Docker Compose 설정
└── .env.example           # 환경 변수 예시
```

## 기능

- **인증**: Keycloak 연동 (JWT 검증 및 Admin API 연동)
  - JWT 토큰 검증
  - 로그인/회원가입 API
  - 사용자 목록 조회 (관리자)
  - 사용자 정보 조회
- **검색**: Meilisearch 연동
- **API**: FastAPI 기반 RESTful API

## 시작하기

### 로컬 개발

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정 추가
```

4. 서버 실행
```bash
# 방법 1: 스크립트 사용
bash scripts/run_server.sh

# 방법 2: 직접 실행
python main.py

# 방법 3: uvicorn 직접 실행
uvicorn main:app --reload
```

### Docker 사용

1. Docker Compose로 실행
```bash
docker-compose up -d
```

서비스:
- **Keycloak**: http://localhost:8080 (관리자: admin/admin)
- **Meilisearch**: http://localhost:7700 (API Key: masterKey123)
- **Backend API**: http://localhost:8000

2. Docker로 직접 실행
```bash
docker build -t backend-api .
docker run -p 8000:8000 --env-file .env backend-api
```

## API 문서

### 로컬 개발 환경

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### 프로덕션 환경 (Kubernetes)

프로덕션 환경에서는 다음 URL로 접근할 수 있습니다:

- Swagger UI: `https://api.matchacake.click/docs`
- OpenAPI JSON: `https://api.matchacake.click/api/openapi.json`

### Swagger UI 설정

Backend API는 Ingress를 통해 `/api` prefix로 접근되므로, Swagger UI가 올바르게 작동하도록 다음과 같이 설정되어 있습니다:

1. **FastAPI 설정**:
   - `root_path="/api"`: Ingress의 `/api` prefix를 인식
   - `openapi_url="/openapi.json"`: `root_path`가 자동으로 적용되어 실제로는 `/api/openapi.json`이 됨

2. **커스텀 경로**:
   - `/docs`: 루트 경로의 Swagger UI (Ingress를 통해 `/api/docs`로 접근 가능)
   - `/api/docs`: 명시적인 `/api` prefix 경로
   - `/api/openapi.json`: OpenAPI 스키마 엔드포인트

**주의사항**: `ROOT_PATH="/api"` 환경 변수가 설정되어 있으므로, `openapi_url`은 `/openapi.json`만 지정하면 자동으로 `/api/openapi.json`이 됩니다.

## 환경 변수

`.env.example` 파일을 참고하여 필요한 환경 변수를 설정하세요.

### 로컬 개발 환경 예시

```env
# Application
APP_NAME=Backend API
APP_VERSION=1.0.0
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000

# Keycloak (인증 서버)
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=backend-client
KEYCLOAK_CLIENT_SECRET=  # Public client는 비워둠

# Keycloak Admin API (관리자 API 접근용)
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# JWT
JWT_ALGORITHM=RS256

# Meilisearch (검색 서버)
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_API_KEY=masterKey123
```

## Keycloak 설정 가이드

### 로컬 개발 환경

#### 1. Docker Compose로 Keycloak 시작

```bash
docker-compose up -d
```

#### 2. master realm에 admin 사용자 생성 (필수)

Backend API에서 Keycloak Admin API를 사용하려면 master realm에 admin 사용자가 필요합니다.

**단계:**

1. Keycloak Admin Console 접속: http://localhost:8080
2. "Administration Console" 클릭
3. Username: `admin`, Password: `admin`으로 로그인
4. **현재 위치 확인**: 왼쪽 상단에서 "master" realm이 선택되어 있는지 확인
5. **Users 메뉴 클릭**: 왼쪽 메뉴에서 "Users" 클릭
6. **Create new user 클릭**: 오른쪽 상단의 "Create new user" 버튼 클릭
7. **사용자 정보 입력**:
   - Username: `admin` 입력
   - Email: `admin@example.com` (선택사항)
   - **Enabled**: `ON`으로 설정 (중요!)
   - "Create" 버튼 클릭
8. **비밀번호 설정**:
   - "Credentials" 탭 클릭
   - Password: `admin` 입력
   - Password confirmation: `admin` 입력
   - **Temporary**: `OFF`로 설정 (중요! 임시 비밀번호가 아니도록)
   - "Set password" 버튼 클릭

#### 3. my-realm 생성

1. 왼쪽 상단의 "Add realm" 버튼 클릭
2. Realm name: `my-realm` 입력
3. "Create" 버튼 클릭

#### 4. backend-client 생성 (my-realm에서)

1. **my-realm 선택**: 왼쪽 상단에서 "my-realm" 선택
2. **Clients 메뉴 클릭**: 왼쪽 메뉴에서 "Clients" 클릭
3. **Create client 클릭**: 오른쪽 상단의 "Create client" 버튼 클릭
4. **General settings**:
   - Client type: `OpenID Connect` 선택
   - Client ID: `backend-client` 입력
   - "Next" 버튼 클릭
5. **Capability config**:
   - Client authentication: `Off` (Public client)
   - Authorization: `Off`
   - Standard flow: `ON` (체크)
   - Direct access grants: `ON` (체크) - **중요!**
   - "Next" 버튼 클릭
6. **Login settings**:
   - Root URL: 비워두기
   - Home URL: 비워두기
   - Valid redirect URIs: `http://localhost:8000/*` 입력
   - Web origins: `http://localhost:8000` 입력
   - "Save" 버튼 클릭

#### 5. Realm Authentication Flow 설정 (중요!)

**⚠️ 계속 오류가 발생하면 Realm을 새로 만드는 것이 가장 확실합니다!**

1. `my-realm` → **"Authentication"** → **"Flows"** 탭 클릭
2. **"direct grant"** flow 찾아서 클릭
3. **"Flow: Direct Grant - Conditional OTP" 완전히 제거**:
   - "Direct Grant - Conditional OTP" 행의 **톱니바퀴 아이콘** 클릭
   - **"Delete"** 클릭 (확인 메시지에서도 Delete)
   - ⚠️ "Disabled"로 두면 안 됩니다! 완전히 삭제!
4. **"Execution: Password"** 확인:
   - **"Required"**로 설정되어 있는지 확인
5. **Save** 클릭

#### 6. 테스트 사용자 생성 (my-realm에서)

1. **Users 메뉴 클릭**: 왼쪽 메뉴에서 "Users" 클릭
2. **Create new user 클릭**: 오른쪽 상단의 "Create new user" 버튼 클릭
3. **사용자 정보 입력**:
   - Username: `testuser` 입력
   - **Email**: `test@example.com` 입력 (반드시 입력!)
   - **First name**: `Test` (중요! "Account is not fully set up" 오류 방지)
   - **Last name**: `User` (중요! "Account is not fully set up" 오류 방지)
   - **Email verified**: `ON`으로 설정
   - **Enabled**: `ON`으로 설정
   - "Create" 버튼 클릭
4. **비밀번호 설정**:
   - "Credentials" 탭 클릭
   - Password: `testuser` 입력
   - Password confirmation: `testuser` 입력
   - **Temporary**: `OFF`로 설정 (중요!)
   - "Set password" 버튼 클릭
5. **Required Actions 확인**:
   - **"Details" 탭** 클릭
   - 아래로 스크롤하여 **"Required user actions"** 섹션 찾기
   - 모든 항목이 비어있는지 확인 (필요시 제거)
   - Save 클릭

**⚠️ 중요:** Keycloak 26.x 버전에서는 "Condition - user configured"가 First name과 Last name이 설정되어 있는지 확인합니다. 이 필드들이 비어있으면 "Account is not fully set up" 오류가 발생할 수 있습니다!

#### 7. JWT 토큰 발급 테스트

```bash
# Public Client (권장)
curl -X POST "http://localhost:8080/realms/my-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-client" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testuser"
```

성공 응답:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_token": "...",
  "token_type": "Bearer"
}
```

### 프로덕션 환경 (Kubernetes)

#### 현재 설정
- **Keycloak URL**: `https://api.matchacake.click/keycloak`
- **Realm**: `formation-lap` (프로덕션용)
- **Client ID**: `backend-client`

#### 토큰 발급 방법

**방법 1: Keycloak에 직접 토큰 요청 (권장)**

```bash
curl -X POST https://api.matchacake.click/keycloak/realms/formation-lap/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&client_id=backend-client&username=<username>&password=<password>" \
  -k | jq .
```

**방법 2: Backend API를 통한 토큰 발급**

```bash
# 1. 회원가입
curl -X POST https://api.matchacake.click/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test12345",
    "region_code": "KR",
    "subscription_status": "free"
  }'

# 2. 로그인 및 토큰 발급
curl -X POST https://api.matchacake.click/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test12345"
  }'
```

#### 토큰 사용 방법

발급받은 토큰을 사용하여 인증이 필요한 API를 호출할 수 있습니다:

```bash
curl -H "Authorization: Bearer <access_token>" \
  https://api.matchacake.click/api/v1/users/me
```

**Swagger UI에서 테스트:**
1. `https://api.matchacake.click/docs` 접속
2. 오른쪽 상단의 "Authorize" 버튼 클릭
3. 발급받은 토큰을 입력: `Bearer <access_token>`
4. "Authorize" 클릭
5. 인증이 필요한 API 엔드포인트 테스트

## Kubernetes 배포 가이드

### EKS 워커 노드에 파드 배포

Backend API를 EKS 워커 노드에 파드로 배포하는 방법입니다.

#### 1. ECR 이미지 준비

```bash
# ECR 리포지토리 생성 (이미 있다면 생략)
aws ecr create-repository \
  --repository-name backend-api \
  --region ap-northeast-2

# Docker 이미지 빌드
cd /root/Backend
docker build -t backend-api:latest .

# ECR에 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 태그 및 푸시
ECR_REPO=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-2.amazonaws.com/backend-api
docker tag backend-api:latest $ECR_REPO:latest
docker push $ECR_REPO:latest
```

#### 2. 배포 확인

```bash
# 파드 상태 확인
kubectl get pods -n formation-lap -l app=backend-api

# 서비스 확인
kubectl get svc -n formation-lap backend-api-service

# 로그 확인
kubectl logs -n formation-lap -l app=backend-api --tail=50

# Ingress 확인
kubectl get ingress -n formation-lap msa-ingress
```

#### 3. 접근 경로

**외부 접근:**
- ALB를 통한 접근: `https://api.matchacake.click/api/v1/health`

**클러스터 내부 접근:**
- 서비스 이름: `backend-api-service.formation-lap.svc.cluster.local:8000`
- 단축 이름: `backend-api-service:8000` (같은 네임스페이스 내)

### 환경 변수 (Kubernetes)

#### ConfigMap (공개 설정)
- `APP_NAME`, `APP_VERSION`, `DEBUG`, `ENVIRONMENT`
- `HOST`, `PORT`
- `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`
- `JWT_ALGORITHM`
- `MEILISEARCH_URL`
- `DB_PORT`, `DB_NAME`

#### Secret (비밀 정보)
- `KEYCLOAK_CLIENT_SECRET`
- `KEYCLOAK_ADMIN_USERNAME`, `KEYCLOAK_ADMIN_PASSWORD`
- `MEILISEARCH_API_KEY`
- `DATABASE_URL` (RDS Proxy endpoint 포함)

### RDS Proxy 사용

Backend API는 RDS Proxy를 통해 데이터베이스에 연결합니다:
- 연결 문자열: `mysql+pymysql://<username>:<password>@<rds-proxy-endpoint>:3306/<db-name>?charset=utf8mb4`
- RDS Proxy endpoint는 Terraform output에서 확인 가능:
  ```bash
  terraform output kor_db_proxy_endpoint
  ```

### Kubernetes 환경 설정

#### 환경별 차이점

**로컬 환경 (Docker Compose)**
- Keycloak: `http://localhost:8080`
- Backend API: `http://localhost:8000`
- DB: Keycloak 내장 H2 (dev-file)
- 설정: `.env` 파일 사용

**Kubernetes 환경**
- Keycloak: Kubernetes Service를 통해 접근
- Backend API: Kubernetes Service를 통해 접근
- DB: 외부 데이터베이스 (PostgreSQL 등) 또는 영구 볼륨
- 설정: ConfigMap, Secret 사용

#### 포트포워딩으로 접근

로컬에서 Kubernetes의 Keycloak에 접근하려면:

```bash
# Keycloak 포트포워딩
kubectl port-forward svc/keycloak 8080:8080 -n formation-lap

# Backend API 포트포워딩
kubectl port-forward svc/backend-service 8000:8000 -n formation-lap
```

## 데이터베이스 연결 문제 해결

### 발견된 문제

**인증 거부 오류 (Access denied)**
- 에러: `Access denied for user 'admin'@'10.23.12.111' (using password: YES)`
- 실제 MySQL 연결 테스트에서 발생

### 해결 방법

#### 방법 1: DB 클러스터 비밀번호 리셋 (권장)

DB 클러스터 비밀번호를 Secrets Manager 비밀번호와 일치시킵니다.

```bash
aws rds modify-db-cluster \
  --region ap-northeast-2 \
  --db-cluster-identifier y2om-kor-aurora-mysql \
  --master-user-password "StrongPassword123!" \
  --apply-immediately
```

**주의사항:**
- 비밀번호 변경 시 클러스터가 잠시 재시작될 수 있음
- 기존 연결이 끊어질 수 있음
- 적용 즉시 변경하려면 `--apply-immediately` 플래그 사용

#### 방법 2: Secrets Manager 비밀번호 업데이트

실제 DB 클러스터 비밀번호를 알고 있다면 Secrets Manager를 업데이트합니다.

```bash
aws secretsmanager put-secret-value \
  --region ap-northeast-2 \
  --secret-id formation-lap/db/dev/credentials \
  --secret-string '{"username":"admin","password":"<actual-db-password>"}'
```

### 연결 테스트

```bash
# 파드에서 연결 테스트
POD_NAME=$(kubectl get pods -n formation-lap -l app=backend-api -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n formation-lap $POD_NAME -- python3 -c "
import pymysql
try:
    conn = pymysql.connect(
        host='y2om-formation-lap-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com',
        port=3306,
        user='admin',
        password='StrongPassword123!',
        database='y2om_db',
        connect_timeout=10
    )
    print('✅ 연결 성공')
    conn.close()
except Exception as e:
    print(f'❌ 연결 실패: {e}')
"
```

### 문제 해결 체크리스트

1. **네트워크 연결 확인**
   - 포트 3306 OPEN 확인
   - 보안 그룹 규칙 확인

2. **RDS Proxy 상태 확인**
   - Proxy 상태: `available`
   - Target 상태: `AVAILABLE`

3. **비밀번호 일치 확인**
   - terraform.tfvars 비밀번호
   - Secrets Manager 비밀번호
   - DB 클러스터 마스터 비밀번호

4. **데이터베이스 존재 확인**
   - `y2om_db` 데이터베이스가 존재하는지 확인
   - 없으면 생성 필요

## 문제 해결 가이드

### "Account is not fully set up" 오류

**증상:**
```json
{"error": "invalid_grant", "error_description": "Account is not fully set up"}
```

**원인:**
- 사용자의 Email 필드가 비어있음
- Required Actions가 설정되어 있음
- Email verified가 OFF
- First name과 Last name이 비어있음 (Keycloak 26.x)
- Authentication Flow 설정 문제

**해결 방법:**

#### 방법 1: 사용자 설정 확인 및 수정

1. **Keycloak Admin Console에서 사용자 확인**
   - my-realm → Users → testuser 클릭
   - Details 탭:
     - **Email**: 반드시 입력되어 있어야 함 (예: `test@example.com`)
     - **First name**: `Test` 입력
     - **Last name**: `User` 입력
     - **Email verified**: `ON`으로 설정
     - **Enabled**: `ON`으로 설정
     - Save 클릭
   - Required Actions 탭:
     - 모든 항목이 비어있는지 확인
     - 체크된 항목이 있으면 모두 제거
     - Save 클릭
   - Credentials 탭:
     - **Temporary**: `OFF`로 설정 확인

#### 방법 2: Authentication Flow 확인 및 수정

**⚠️ 중요: "Direct Grant - Conditional OTP"를 Disabled가 아니라 완전히 삭제해야 합니다!**

1. my-realm → Authentication → Flows
2. "direct grant" flow 선택
3. "Direct Grant - Conditional OTP" 행 찾기
4. 오른쪽의 톱니바퀴 아이콘(설정) 클릭
5. **"Delete" 클릭** (Disabled로 두면 안 됩니다! 완전히 삭제!)
6. 확인 메시지에서 "Delete" 클릭
7. "Save" 클릭

4. "Execution: Password" 확인:
   - "Required"로 설정되어 있는지 확인
   - "Alternative"나 "Disabled"가 아닌지 확인

#### 방법 3: 사용자 재생성 (가장 확실한 방법)

모든 설정이 올바른데도 오류가 발생한다면:

1. Users → testuser → **Delete** 클릭
2. "Create new user" 클릭
3. Username: `testuser` 입력
4. **Email**: `test@example.com` 입력 (반드시!)
5. **First name**: `Test` 입력
6. **Last name**: `User` 입력
7. **Email verified**: `ON`으로 설정
8. **Enabled**: `ON`으로 설정
9. "Create" 클릭
10. "Credentials" 탭:
    - Password: `testuser` 입력
    - Password confirmation: `testuser` 입력
    - **Temporary**: `OFF`로 설정 (중요!)
    - "Set password" 클릭
11. "Details" 탭:
    - "Required user actions" 섹션 확인
    - 모든 항목이 비어있는지 확인
    - Save 클릭

### "user_not_found" 오류

**원인:** master realm에 admin 사용자가 없습니다.

**해결 방법:**
위의 "master realm에 admin 사용자 생성" 섹션을 참고하여 생성하세요.

### "invalid_client" 오류

**원인:** backend-client가 제대로 설정되지 않았습니다.

**해결 방법:**
1. my-realm → Clients → backend-client 확인
2. Direct access grants: `ON` 확인
3. Client authentication: `Off` 확인

### Keycloak 접근 실패

1. Keycloak Pod 상태 확인: `kubectl get pods -n formation-lap -l app=keycloak`
2. Keycloak Service 확인: `kubectl get svc -n formation-lap keycloak-service`
3. Ingress 확인: `kubectl get ingress -n formation-lap keycloak-ingress`
4. ALB DNS 확인: `kubectl get ingress -n formation-lap keycloak-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'`

### Realm 불일치

- Backend API의 `KEYCLOAK_REALM`과 실제 Keycloak realm이 일치하는지 확인
- ConfigMap 업데이트 후 파드 재시작 필요

### JWT Public Key 오류

**증상:**
```
JWKError: Unable to load PEM file
```

**해결 방법:**
1. `.env` 파일의 `JWT_PUBLIC_KEY` 확인
2. Keycloak에서 Public Key 가져오기:
```bash
curl http://localhost:8080/realms/my-realm/protocol/openid-connect/certs
```
3. Backend API 재시작

## 포트포워딩 가이드

### 로컬 개발 환경

로컬 개발 환경에서는 포트포워딩이 필요 없습니다! Keycloak은 이미 `http://localhost:8080`에서 접근 가능합니다.

### Kubernetes 환경에서 포트포워딩

Keycloak이 Kubernetes 클러스터에 배포되어 있는 경우:

```bash
# Keycloak 포트포워딩
kubectl port-forward svc/keycloak 8080:8080 -n formation-lap

# Backend API 포트포워딩
kubectl port-forward svc/backend-service 8000:8000 -n formation-lap

# Meilisearch 포트포워딩
kubectl port-forward svc/meilisearch 7700:7700 -n <namespace>
```

### 접근 확인

```bash
# Keycloak 확인
curl http://localhost:8080/health/ready

# Backend API 확인
curl http://localhost:8000/api/v1/health

# Meilisearch 확인
curl http://localhost:7700/health
```

## 주의사항

- 로그인/회원가입 API는 Keycloak과 연동되어 처리됩니다
- JWT 검증은 Backend에서 담당합니다
- 검색 기능은 Meilisearch와 연동됩니다
- Kubernetes 환경에서는 ConfigMap과 Secret을 사용하여 환경 변수를 관리합니다
