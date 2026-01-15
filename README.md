# Backend API

FastAPI 기반 Backend 애플리케이션

## 목차
1. [프로젝트 구조](#프로젝트-구조)
2. [시작하기](#시작하기)
3. [API 문서](#api-문서)
4. [JWT 토큰 발급 및 사용](#jwt-토큰-발급-및-사용)
5. [S3 영상 파일 관리](#s3-영상-파일-관리)
6. [Meilisearch 검색 기능](#meilisearch-검색-기능)
7. [Kubernetes 배포](#kubernetes-배포)
8. [테스트 가이드](#테스트-가이드)

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

Backend API는 Kubernetes 환경에서 실행되며, Terraform을 통해 자동으로 배포됩니다.

자세한 배포 방법은 [Kubernetes 배포](#kubernetes-배포) 섹션을 참고하세요.

---

## API 문서

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

## S3 영상 파일 관리

### 개요

Backend API는 S3 버킷에 저장된 영상 파일을 관리하고 CloudFront URL을 생성할 수 있습니다.

### 환경 변수 설정

Kubernetes 환경에서 다음 환경 변수가 자동으로 설정됩니다:

- `S3_BUCKET_NAME`: S3 버킷 이름 (예: `y2om-my-origin-bucket-087730891580`)
- `S3_REGION`: S3 버킷 리전 (기본값: `ap-northeast-2`)
- `CLOUDFRONT_DOMAIN`: CloudFront 도메인 (예: `www.exampleott.click`)

### S3 접근 권한

Backend API는 IRSA (IAM Roles for Service Accounts)를 통해 S3에 접근합니다:
- **권한**: `s3:ListBucket`, `s3:GetObject`, `s3:HeadObject`
- **범위**: 읽기 전용 (영상 파일 조회 및 URL 생성)

### API 엔드포인트

#### 1. S3 영상 파일 목록 조회

**엔드포인트**: `GET /api/v1/contents/{content_id}/video-assets/s3/list`

**Query 파라미터**:
- `prefix` (선택): S3 경로 prefix (예: `videos/`, `content/1/`)
- `max_keys` (선택): 최대 반환 개수 (기본값: 1000, 최대: 1000)

**사용 예시**:
```bash
# 1. 토큰 발급
TOKEN=$(curl -s -X POST "https://api.exampleott.click/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}' \
  -k | jq -r '.access_token')

# 2. S3 파일 목록 조회
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.exampleott.click/api/v1/contents/1/video-assets/s3/list?prefix=videos/" \
  -k | jq .
```

**응답 예시**:
```json
[
  {
    "key": "327101_tiny.mp4",
    "size": 1243830,
    "last_modified": "2026-01-15T11:34:14",
    "url": "https://www.exampleott.click/327101_tiny.mp4"
  }
]
```

#### 2. S3 파일 CloudFront URL 조회

**엔드포인트**: `GET /api/v1/contents/{content_id}/video-assets/s3/url/{s3_key}`

**Path 파라미터**:
- `content_id`: 컨텐츠 ID
- `s3_key`: S3 객체 키 (예: `327101_tiny.mp4`, `videos/content1.mp4`)

**사용 예시**:
```bash
# 특정 파일의 CloudFront URL 조회
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.exampleott.click/api/v1/contents/1/video-assets/s3/url/327101_tiny.mp4" \
  -k | jq .
```

**응답 예시**:
```json
{
  "key": "327101_tiny.mp4",
  "size": 1243830,
  "content_type": "video/mp4",
  "last_modified": "2026-01-15T11:34:14",
  "url": "https://www.exampleott.click/327101_tiny.mp4"
}
```

### CloudFront 직접 접근

S3에 저장된 영상 파일은 CloudFront를 통해 직접 접근할 수 있습니다:

```
https://www.exampleott.click/{s3_key}
```

**예시**:
- 파일: `327101_tiny.mp4` (S3 버킷 루트)
- URL: `https://www.exampleott.click/327101_tiny.mp4`

### 지원되는 영상 파일 형식

다음 확장자를 가진 파일만 조회됩니다:
- `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.m4v`, `.flv`

### Swagger UI를 통한 테스트

1. `https://api.exampleott.click/docs` 접속
2. `/api/v1/auth/login` 엔드포인트에서 로그인하여 토큰 발급
3. 우측 상단 "Authorize" 버튼 클릭하여 토큰 입력
4. `/api/v1/contents/{content_id}/video-assets/s3/list` 또는 `/api/v1/contents/{content_id}/video-assets/s3/url/{s3_key}` 엔드포인트 선택
5. "Try it out" 클릭
6. 파라미터 입력 후 "Execute" 클릭

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
- `S3_BUCKET_NAME`, `S3_REGION`, `CLOUDFRONT_DOMAIN`

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

### 프로덕션 환경 (Kubernetes)

환경 변수는 Kubernetes ConfigMap과 Secret을 통해 관리됩니다. 자세한 내용은 Terraform 설정을 참고하세요.

#### ConfigMap (공개 설정)
- `APP_NAME`, `APP_VERSION`, `DEBUG`, `ENVIRONMENT`
- `HOST`, `PORT`
- `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`
- `JWT_ALGORITHM`
- `MEILISEARCH_URL`
- `DB_PORT`, `DB_NAME`
- `S3_BUCKET_NAME`, `S3_REGION`, `CLOUDFRONT_DOMAIN`

#### Secret (비밀 정보)
- `KEYCLOAK_CLIENT_SECRET`
- `KEYCLOAK_ADMIN_USERNAME`, `KEYCLOAK_ADMIN_PASSWORD`
- `MEILISEARCH_API_KEY`
- `DATABASE_URL` (RDS Proxy endpoint 포함)

---

## Keycloak 설정

Keycloak은 Kubernetes 환경에서 자동으로 배포되며, Terraform을 통해 설정됩니다.

### 프로덕션 환경 설정

- **Keycloak URL**: `https://api.exampleott.click/keycloak`
- **Realm**: `formation-lap`
- **Client ID**: `backend-client`
- **Admin Console**: `https://api.exampleott.click/keycloak/admin`

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
