# Backend API

FastAPI 기반 Backend 애플리케이션

## 목차
1. [프로젝트 구조](#프로젝트-구조)
2. [시작하기](#시작하기)
3. [API 문서](#api-문서)
4. [JWT 토큰 발급 및 사용](#jwt-토큰-발급-및-사용)
5. [Meilisearch 검색 기능](#meilisearch-검색-기능)
6. [Kubernetes 배포](#kubernetes-배포)
7. [테스트 가이드](#테스트-가이드)

---

## 프로젝트 구조

```
Backend/
├── app/
│   ├── core/              # 핵심 설정 및 보안
│   │   ├── config.py      # 애플리케이션 설정
│   │   ├── database.py    # 데이터베이스 연결
│   │   └── security.py    # JWT 검증
│   ├── api/               # API 라우터
│   │   └── v1/
│   │       └── routes/    # API 엔드포인트
│   ├── services/          # 외부 서비스 연동
│   │   ├── auth.py        # Keycloak 연동
│   │   ├── search.py      # Meilisearch 연동
│   │   └── user_service.py # 사용자 서비스
│   ├── models/            # 데이터 모델
│   └── schemas/           # Pydantic 스키마
├── alembic/               # 데이터베이스 마이그레이션
├── scripts/               # 유틸리티 스크립트
├── main.py                # 애플리케이션 진입점
├── requirements.txt       # Python 의존성
├── Dockerfile             # Docker 이미지 빌드
└── docker-compose.yml     # Docker Compose 설정
```

---

## 시작하기

### 로컬 개발

1. **가상환경 생성 및 활성화**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일을 편집하여 필요한 설정 추가
   ```

4. **서버 실행**
   ```bash
   # 방법 1: 스크립트 사용
   bash scripts/run_server.sh
   
   # 방법 2: 직접 실행
   python main.py
   
   # 방법 3: uvicorn 직접 실행
   uvicorn main:app --reload
   ```

### Docker 사용

```bash
# Docker Compose로 실행
docker-compose up -d
```

서비스:
- **Keycloak**: http://localhost:8080 (관리자: admin/admin)
- **Meilisearch**: http://localhost:7700 (API Key: masterKey123)
- **Backend API**: http://localhost:8000

---

## API 문서

### 로컬 개발 환경

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### 프로덕션 환경 (Kubernetes)

- Swagger UI: `https://api.exampleott.click/docs`
- OpenAPI JSON: `https://api.exampleott.click/openapi.json`

---

## JWT 토큰 발급 및 사용

### 프로덕션 환경 설정

- **Keycloak URL**: `https://api.exampleott.click/keycloak`
- **Realm**: `formation-lap`
- **Client ID**: `backend-client`
- **Backend API URL**: `https://api.exampleott.click/api`

### 토큰 발급 방법

#### 방법 1: Backend API를 통한 토큰 발급 (권장)

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

```bash
curl -X POST https://api.exampleott.click/keycloak/realms/formation-lap/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=backend-client" \
  -d "username=user@example.com" \
  -d "password=your-password" \
  -k | jq .
```

### 토큰 사용 방법

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

1. `https://api.exampleott.click/docs` 접속
2. 오른쪽 상단의 **"Authorize"** 버튼 클릭
3. 발급받은 토큰을 입력: `Bearer <access_token>`
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

### 사용자 ID 매핑 (Keycloak → Database)

Backend API는 Keycloak에서 발급한 JWT 토큰의 사용자 정보를 데이터베이스의 사용자 ID로 매핑합니다.

#### 작동 방식

1. **JWT 토큰에서 email 추출**: JWT 페이로드의 `email` 필드를 읽습니다.
2. **데이터베이스에서 사용자 조회**: `users` 테이블에서 해당 `email`로 사용자를 조회합니다.
3. **DB user_id 반환**: 조회된 사용자의 `id`를 반환합니다.

#### 중요 사항

- **회원가입 필수**: JWT 토큰이 발급되었더라도, Backend API의 `users` 테이블에 해당 사용자가 등록되어 있어야 합니다.
- **Email 기반 매핑**: Keycloak의 `sub` (user ID)가 아닌 `email` 필드를 사용하여 매핑합니다.
- **자동 처리**: `watch_history`, `content_likes` 등 모든 엔드포인트에서 자동으로 처리됩니다.

---

## Meilisearch 검색 기능

### Meilisearch란?

Meilisearch는 빠른 검색 엔진으로, Backend API의 `/api/v1/search` 엔드포인트에서 사용됩니다.

### Kubernetes 배포

Meilisearch는 Terraform을 통해 자동으로 배포됩니다.

#### 배포 확인

```bash
# Meilisearch Pod 확인
kubectl get pods -n formation-lap -l app=meilisearch

# Meilisearch Service 확인
kubectl get svc -n formation-lap meilisearch-service

# Meilisearch 로그 확인
kubectl logs -n formation-lap -l app=meilisearch --tail=50
```

### Search API 사용 방법

#### Swagger UI를 통한 테스트 (권장)

1. `https://api.exampleott.click/docs` 접속
2. `/api/v1/auth/login` 엔드포인트에서 로그인하여 토큰 발급
3. 우측 상단 "Authorize" 버튼 클릭하여 토큰 입력
4. `/api/v1/search` 엔드포인트 선택
5. "Try it out" 클릭
6. `q` 파라미터에 검색어 입력 (예: "test", "영화")
7. "Execute" 클릭하여 결과 확인

#### curl을 통한 테스트

```bash
# 1. 토큰 발급
TOKEN=$(curl -s -X POST "https://api.exampleott.click/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}' \
  -k | jq -r '.access_token')

# 2. 컨텐츠 생성 (자동으로 Meilisearch에 인덱싱됨)
curl -X POST "https://api.exampleott.click/api/v1/contents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "테스트 영화",
    "description": "검색 테스트를 위한 영화입니다",
    "age_rating": "ALL"
  }' \
  -k | jq .

# 3. 검색 실행
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.exampleott.click/api/v1/search?q=테스트" \
  -k | jq .
```

**응답 예시:**
```json
{
  "hits": [
    {
      "title": "테스트 영화",
      "description": "검색 테스트를 위한 영화입니다",
      "age_rating": "ALL",
      "id": 1,
      "like_count": 0,
      "created_at": "2026-01-15T11:01:20",
      "updated_at": "2026-01-15T11:01:20"
    }
  ],
  "query": "테스트",
  "processing_time_ms": 0,
  "limit": 20,
  "offset": 0,
  "estimated_total_hits": 1
}
```

### 자동 인덱싱

Backend API에서 컨텐츠를 생성/수정/삭제할 때 자동으로 Meilisearch 인덱스에 동기화됩니다.

---

## Kubernetes 배포

### ECR 이미지 준비

```bash
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

### 배포 확인

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

### 접근 경로

**외부 접근:**
- ALB를 통한 접근: `https://api.exampleott.click/api/v1/health`
- Swagger UI: `https://api.exampleott.click/docs`

**클러스터 내부 접근:**
- 서비스 이름: `backend-api-service.formation-lap.svc.cluster.local:8000`
- 단축 이름: `backend-api-service:8000` (같은 네임스페이스 내)

### 환경 변수

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
- RDS Proxy endpoint는 Terraform output에서 확인 가능

---

## 테스트 가이드

### 1. API 엔드포인트 테스트

#### Swagger UI를 통한 테스트 (권장)

1. **Swagger UI 접속**
   ```
   https://api.exampleott.click/docs
   ```

2. **인증 토큰 발급**
   - `/api/v1/auth/login` 엔드포인트에서 로그인
   - 응답에서 `access_token` 복사
   - 우측 상단 "Authorize" 버튼 클릭하여 토큰 입력

3. **API 테스트**
   - 원하는 엔드포인트 선택
   - "Try it out" 클릭
   - 파라미터 입력 후 "Execute" 클릭

#### Search API 테스트

1. **컨텐츠 생성**
   - `/api/v1/contents` (POST) 엔드포인트 사용
   - Request body 예시:
     ```json
     {
       "title": "테스트 영화",
       "description": "검색 테스트를 위한 영화입니다",
       "age_rating": "ALL"
     }
     ```

2. **검색 테스트**
   - `/api/v1/search` (GET) 엔드포인트 사용
   - `q` 파라미터에 검색어 입력 (예: "테스트", "영화")
   - 결과 확인

#### curl을 통한 테스트

```bash
# 1. 토큰 발급
TOKEN=$(curl -s -X POST "https://api.exampleott.click/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test7@example.com", "password": "test1234"}' \
  -k | jq -r '.access_token')

# 2. Search API 테스트
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.exampleott.click/api/v1/search?q=test" \
  -k | jq .

# 3. 컨텐츠 생성
curl -X POST "https://api.exampleott.click/api/v1/contents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "테스트 영화", "description": "검색 테스트", "age_rating": "ALL"}' \
  -k | jq .
```

### 2. 인프라 상태 확인

#### Kubernetes 리소스 확인

```bash
# 모든 Pod 상태
kubectl get pods -n formation-lap

# Backend API Pod
kubectl get pods -n formation-lap -l app=backend-api

# Meilisearch Pod
kubectl get pods -n formation-lap -l app=meilisearch

# Service 확인
kubectl get svc -n formation-lap

# Ingress 확인
kubectl get ingress -n formation-lap
```

#### 로그 확인

```bash
# Backend API 로그
kubectl logs -n formation-lap -l app=backend-api --tail=50

# Meilisearch 로그
kubectl logs -n formation-lap -l app=meilisearch --tail=50
```

### 3. Meilisearch 직접 테스트

```bash
# Meilisearch Pod에 접속
MEILI_POD=$(kubectl get pod -n formation-lap -l app=meilisearch -o jsonpath='{.items[0].metadata.name}')

# Health Check
kubectl exec -n formation-lap $MEILI_POD -- curl -s http://localhost:7700/health

# 인덱스 확인
kubectl exec -n formation-lap $MEILI_POD -- \
  curl -s -H "Authorization: Bearer masterKey1234567890" \
  http://localhost:7700/indexes
```

### 4. 문제 해결

#### "Search service is not available" 오류

**해결 방법:**
1. Meilisearch Pod가 실행 중인지 확인:
   ```bash
   kubectl get pods -n formation-lap -l app=meilisearch
   ```
2. Meilisearch Service가 존재하는지 확인:
   ```bash
   kubectl get svc -n formation-lap meilisearch-service
   ```
3. Backend API의 환경 변수 확인:
   ```bash
   kubectl get pod -n formation-lap -l app=backend-api -o jsonpath='{.items[0].metadata.name}' | \
     xargs -I {} kubectl exec -n formation-lap {} -- env | grep MEILISEARCH
   ```

#### "User not found in database" 오류

JWT 토큰은 유효하지만 데이터베이스에 사용자가 등록되어 있지 않은 경우입니다.

**해결 방법:**
1. 회원가입 API를 통해 사용자 등록:
   ```bash
   curl -X POST https://api.exampleott.click/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "password",
       "first_name": "First",
       "last_name": "Last",
       "region_code": "KR",
       "subscription_status": "free"
     }' \
     -k | jq .
   ```

---

## 환경 변수

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
KEYCLOAK_REALM=formation-lap
KEYCLOAK_CLIENT_ID=backend-client
KEYCLOAK_CLIENT_SECRET=

# Keycloak Admin API
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# JWT
JWT_ALGORITHM=RS256

# Meilisearch (검색 서버)
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_API_KEY=masterKey1234567890

# Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname?charset=utf8mb4
```

### 프로덕션 환경 (Kubernetes)

환경 변수는 Kubernetes ConfigMap과 Secret을 통해 관리됩니다. 자세한 내용은 Terraform 설정을 참고하세요.

---

## Keycloak 설정

### 로컬 개발 환경

Docker Compose를 사용하는 경우, Keycloak이 자동으로 시작됩니다.

1. **Keycloak Admin Console 접속**: http://localhost:8080
2. **관리자 로그인**: Username: `admin`, Password: `admin`
3. **Realm 생성**: `formation-lap` realm 생성
4. **Client 생성**: `backend-client` 생성 (Public client)
5. **사용자 생성**: 테스트용 사용자 생성

자세한 설정 방법은 Keycloak 공식 문서를 참고하세요.

---

## 주의사항

- 로그인/회원가입 API는 Keycloak과 연동되어 처리됩니다
- JWT 검증은 Backend에서 담당합니다
- 검색 기능은 Meilisearch와 연동됩니다
- Kubernetes 환경에서는 ConfigMap과 Secret을 사용하여 환경 변수를 관리합니다
- 사용자는 Keycloak에 등록된 후 Backend API의 `users` 테이블에도 등록되어야 합니다

---

## 추가 리소스

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Keycloak 공식 문서](https://www.keycloak.org/documentation)
- [Meilisearch 공식 문서](https://www.meilisearch.com/docs)
- [Terraform 인프라 README.md](../Terraform/README.md)
