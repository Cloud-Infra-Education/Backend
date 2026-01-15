# Backend API

FastAPI 기반 백엔드 API 서버입니다.

## 📋 개요

이 프로젝트는 OTT 플랫폼을 위한 백엔드 API를 제공합니다. Keycloak을 통한 인증/인가, 비디오 처리, 사용자 관리 등의 기능을 포함합니다.

## 🏗️ 프로젝트 구조

```
Backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── routes/          # API 라우트
│   │           ├── auth.py      # 인증/인가
│   │           ├── users.py     # 사용자 관리
│   │           ├── contents.py  # 컨텐츠 관리
│   │           └── contents_internal.py  # 내부 API (Lambda용)
│   ├── core/                    # 핵심 설정
│   ├── models/                  # 데이터베이스 모델
│   ├── schemas/                 # Pydantic 스키마
│   ├── services/                # 비즈니스 로직
│   └── video-service/           # 비디오 서비스 (별도 FastAPI 앱)
├── lambda/
│   ├── video-processor/         # 비디오 처리 Lambda 함수
│   └── alert-service/           # 알림 서비스 Lambda 함수
├── .github/
│   └── workflows/
│       └── ci-ecr.yml          # CI/CD 워크플로우 (Trivy 스캔 포함)
└── Dockerfile                   # Docker 이미지 빌드
```

## 🚀 주요 기능

### 1. 인증 및 인가
- **Keycloak 통합**: JWT 기반 인증
- **사용자 자동 생성**: 회원가입/로그인 시 Keycloak에 자동 사용자 생성
- **토큰 검증**: RS256 알고리즘을 사용한 JWT 토큰 검증

### 2. 비디오 처리 시스템
- **Lambda 기반 자동 처리**: S3에 비디오 업로드 시 자동 실행
- **메타데이터 추출**: FFprobe를 사용한 영상 길이(duration) 추출
- **썸네일 생성**: FFmpeg를 사용한 썸네일 생성 (5초 지점)
- **데이터베이스 저장**: `video_assets`, `contents` 테이블에 자동 저장
- **TMDB API 연동**: 영화/드라마 메타데이터 자동 가져오기 (선택)

### 3. Video Service
- **비디오 검색**: `GET /videos/search/` - 제목/설명 검색
- **비디오 상세 조회**: `GET /videos/watch/{video_id}`
- **S3 URL 변환**: s3:// 경로를 HTTPS URL로 자동 변환

### 4. Contents Internal API
- **내부 Upsert API**: `PUT /api/v1/contents/{content_id}/upsert-internal`
- **Lambda 연동**: Lambda 함수에서 호출하는 내부 API
- **토큰 인증**: `INTERNAL_TOKEN` 헤더를 통한 보안 인증

## 🔧 환경 변수

### 필수 환경 변수

```bash
# 데이터베이스
DATABASE_URL=mysql+pymysql://user:password@host:port/dbname

# Keycloak
KEYCLOAK_URL=https://api.exampleott.click/keycloak
KEYCLOAK_REALM=formation-lap
KEYCLOAK_CLIENT_ID=backend-client
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# 내부 API 토큰 (Lambda와 공유)
INTERNAL_TOKEN=formation-lap-internal-token-2024-secret-key

# S3
S3_BUCKET_NAME=y2om-my-origin-bucket-087730891580
S3_REGION=ap-northeast-2

# Meilisearch
MEILISEARCH_URL=http://meilisearch-service:7700
MEILISEARCH_API_KEY=masterKey1234567890
```

## 🐳 Docker 빌드 및 배포

### 로컬 빌드

```bash
docker build -t backend-api:latest .
docker run -p 8000:8000 --env-file .env backend-api:latest
```

### ECR 배포

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 087730891580.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 빌드 및 태깅
docker build -t backend-api:latest .
docker tag backend-api:latest 087730891580.dkr.ecr.ap-northeast-2.amazonaws.com/backend-api:latest

# ECR에 푸시
docker push 087730891580.dkr.ecr.ap-northeast-2.amazonaws.com/backend-api:latest
```

## 🔒 보안 스캔 (Trivy)

### CI/CD 통합

GitHub Actions를 통해 자동으로 Trivy 보안 스캔이 실행됩니다:

- **트리거**: `main` 또는 `feat/#*` 브랜치에 push 시
- **스캔 대상**: `backend-api`, `video-service` Docker 이미지
- **심각도**: CRITICAL, HIGH 취약점 검사
- **실패 처리**: 스캔 실패 시 빌드 중단

### 워크플로우 동작

```
1. GitHub Push
   ↓
2. ECR 리포지토리 존재 여부 확인
   ↓
3. Docker 이미지 빌드
   ↓
4. Trivy 보안 스캔 (CRITICAL, HIGH)
   ↓
5. 스캔 통과 → ECR 푸시
   스캔 실패 → 빌드 중단
```

### 수동 스캔

```bash
# Trivy 설치
brew install trivy  # macOS
# 또는
sudo apt-get install trivy  # Ubuntu

# 이미지 스캔
trivy image backend-api:latest

# 특정 심각도만 검사
trivy image --severity CRITICAL,HIGH backend-api:latest
```

## 📡 API 엔드포인트

### 인증
- `POST /api/v1/auth/register` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `GET /api/v1/auth/me` - 현재 사용자 정보

### 컨텐츠
- `GET /api/v1/contents` - 컨텐츠 목록 조회
- `GET /api/v1/contents/{id}` - 컨텐츠 상세 조회
- `PUT /api/v1/contents/{id}/upsert-internal` - 내부 Upsert API (Lambda용)

### 비디오 (Video Service)
- `GET /videos/search/` - 비디오 검색
- `GET /videos/search/?q=검색어` - 검색어로 비디오 검색
- `GET /videos/watch/{video_id}` - 비디오 상세 조회

### Health Check
- `GET /api/v1/health` - 서비스 상태 확인

## 🎬 비디오 처리 워크플로우

```
1. 사용자가 S3에 비디오 업로드
   └─> videos/{content_id}_{slug}.mp4
       예: videos/1_inception.mp4

2. S3 Event Trigger
   └─> Lambda 함수 자동 실행

3. Lambda 처리
   ├─> S3에서 비디오 다운로드 (/tmp)
   ├─> FFprobe로 duration 추출
   ├─> FFmpeg로 썸네일 생성 (5초 지점)
   ├─> 썸네일을 S3 thumbnails/ 경로에 업로드
   ├─> FastAPI upsert API 호출
   │   └─> contents 테이블에 title/description/age_rating 저장
   └─> video_assets 테이블에 데이터 저장

4. 완료
   └─> CloudWatch 로그에 결과 기록
```

## 🧪 테스트

### 로컬 테스트

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API 테스트

```bash
# Health Check
curl http://localhost:8000/api/v1/health

# 회원가입
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# 로그인
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## 📚 문서

- **API 문서**: `https://api.exampleott.click/docs` (Swagger UI)
- **OpenAPI 스키마**: `https://api.exampleott.click/api/openapi.json`
- **아키텍처 설명**: `ARCHITECTURE_EXPLANATION.md`
- **전체 워크플로우**: `COMPLETE_WORKFLOW.md`
- **프론트엔드 가이드**: `FRONTEND_API_GUIDE.md`

## 🔗 관련 저장소

- **Manifests**: [Cloud-Infra-Education/Manifests](https://github.com/Cloud-Infra-Education/Manifests)
- **Terraform**: 인프라 코드

## 📝 주요 변경사항

### v1.0.0
- ✅ Keycloak 통합 및 JWT 인증
- ✅ 사용자 자동 생성 기능
- ✅ 비디오 처리 시스템 (Lambda)
- ✅ Video Service 추가
- ✅ Contents Internal API 추가
- ✅ Trivy 보안 스캔 CI/CD 통합

## 🛠️ 문제 해결

### Keycloak 연결 실패
- Keycloak URL 및 Realm 설정 확인
- 네트워크 연결 확인 (VPC, Security Group)

### 데이터베이스 연결 실패
- RDS Proxy 엔드포인트 확인
- 데이터베이스 자격 증명 확인
- VPC 보안 그룹 규칙 확인

### Lambda에서 FastAPI 호출 실패
- `INTERNAL_TOKEN` 환경 변수 확인
- VPC DNS 설정 확인
- 내부 네트워크 경로 확인

## 📞 연락처

문제가 발생하면 이슈를 생성하거나 팀에 문의하세요.
