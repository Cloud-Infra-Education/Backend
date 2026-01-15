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

- Swagger UI: `https://api.exampleott.click/api/docs`
- OpenAPI JSON: `https://api.exampleott.click/api/openapi.json`

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

#### 7. 테스트 사용자로 로그인 테스트

Backend API를 통해 로그인하여 JWT 토큰을 발급받을 수 있습니다:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testuser"
  }' | jq .
```

성공 응답:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 300
}
```

## JWT 토큰 발급 및 사용 가이드

### 프로덕션 환경 (Kubernetes)

#### 현재 설정
- **Keycloak URL**: `https://api.exampleott.click/keycloak`
- **Realm**: `formation-lap`
- **Client ID**: `backend-client`
- **Backend API URL**: `https://api.exampleott.click/api`

### JWT 토큰 발급 방법

#### 방법 1: Backend API를 통한 토큰 발급 (권장)

Backend API의 로그인 엔드포인트를 사용하면 Keycloak과 자동으로 연동되어 토큰을 발급받을 수 있습니다.

**1단계: 회원가입**

```bash
curl -X POST https://api.exampleott.click/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password",
    "first_name": "First",
    "last_name": "Last",
    "region_code": "KR",
    "subscription_status": "free"
  }' \
  -k | jq .
```

**2단계: 로그인 및 토큰 발급**

```bash
curl -X POST https://api.exampleott.click/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your-password"
  }' \
  -k | jq .
```

**성공 응답:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIweW1sdEltS3dtaVU4RlNlY0dnVFdvcGV5SEhHM0luX085SThmcFZzcWt3In0...",
  "token_type": "bearer",
  "expires_in": 300
}
```

#### 방법 2: Keycloak에 직접 토큰 요청

Keycloak의 토큰 엔드포인트를 직접 호출할 수도 있습니다.

```bash
curl -X POST https://api.exampleott.click/keycloak/realms/formation-lap/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=backend-client" \
  -d "username=user@example.com" \
  -d "password=your-password" \
  -k | jq .
```

### JWT 토큰 사용 방법

발급받은 토큰을 사용하여 인증이 필요한 API를 호출할 수 있습니다.

#### curl을 사용한 API 호출

```bash
# 토큰 변수에 저장
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIweW1sdEltS3dtaVU4RlNlY0dnVFdvcGV5SEhHM0luX085SThmcFZzcWt3In0..."

# 현재 사용자 정보 조회
curl -H "Authorization: Bearer $TOKEN" \
  https://api.exampleott.click/api/v1/users/me \
  -k | jq .

# 시청 기록 조회
curl -H "Authorization: Bearer $TOKEN" \
  https://api.exampleott.click/api/v1/watch-history \
  -k | jq .
```

#### Swagger UI에서 테스트

1. `https://api.exampleott.click/api/docs` 접속
2. 오른쪽 상단의 **"Authorize"** 버튼 클릭
3. 발급받은 토큰을 입력: `Bearer <access_token>`
   - 예: `Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICIweW1sdEltS3dtaVU4RlNlY0dnVFdvcGV5SEhHM0luX085SThmcFZzcWt3In0...`
4. **"Authorize"** 클릭
5. 인증이 필요한 API 엔드포인트 테스트

### JWT 토큰 검증 작동 방식

Backend API는 다음과 같은 방식으로 JWT 토큰을 검증합니다:

1. **토큰 헤더에서 Key ID (kid) 추출**: JWT 헤더의 `kid` 필드를 읽어 어떤 공개 키를 사용해야 하는지 확인합니다.
2. **Keycloak JWKS에서 공개 키 가져오기**: Keycloak의 `/realms/{realm}/protocol/openid-connect/certs` 엔드포인트에서 JWKS (JSON Web Key Set)를 가져옵니다.
3. **올바른 키 선택**: `kid`와 일치하는 서명용 키(`use: sig`)를 선택합니다.
4. **토큰 검증**: 
   - 서명 검증 (RS256 알고리즘)
   - 만료 시간 검증
   - Issuer 검증 (`https://api.exampleott.click/keycloak/realms/formation-lap`)

### 로컬 개발 환경

로컬 개발 환경에서도 동일한 방식으로 토큰을 발급받을 수 있습니다:

```bash
# 로그인
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test1234"
  }' | jq .
```

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
- ALB를 통한 접근: `https://api.exampleott.click/api/v1/health`

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


## 포트포워딩 가이드

### Kubernetes 환경에서 포트포워딩

로컬에서 Kubernetes 서비스에 접근하려면 포트포워딩을 사용할 수 있습니다:

```bash
# Keycloak 포트포워딩
kubectl port-forward svc/keycloak-service 8080:8080 -n formation-lap

# Backend API 포트포워딩
kubectl port-forward svc/backend-api-service 8000:8000 -n formation-lap
```

## 주의사항

- 로그인/회원가입 API는 Keycloak과 연동되어 처리됩니다
- JWT 검증은 Backend에서 담당합니다
- 검색 기능은 Meilisearch와 연동됩니다
- Kubernetes 환경에서는 ConfigMap과 Secret을 사용하여 환경 변수를 관리합니다

## Keycloak 사용자 자동 생성

회원가입 및 로그인 시 Keycloak에 사용자가 자동으로 생성됩니다.

### 기능

- **회원가입 시**: 데이터베이스에 사용자 생성 후 Keycloak에도 자동 생성
- **로그인 시**: Keycloak에 사용자가 없으면 자동 생성 후 토큰 발급

### 구현 세부사항

- `create_keycloak_user()` 함수: Keycloak Admin API를 사용하여 사용자 생성
- `subprocess`와 `curl`을 사용하여 Keycloak Admin API 호출
- 환경 변수에서 Keycloak 설정 읽기:
  - `KEYCLOAK_URL`: Keycloak 서버 URL
  - `KEYCLOAK_REALM`: Keycloak Realm 이름
  - `KEYCLOAK_ADMIN_USERNAME`: Admin 사용자명
  - `KEYCLOAK_ADMIN_PASSWORD`: Admin 비밀번호

### 관련 파일

- `app/api/v1/routes/auth.py`: 회원가입/로그인 엔드포인트
- `Dockerfile`: curl 패키지 포함
