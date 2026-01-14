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
  - 사용자 목록 조회 (관리자)
  - 사용자 정보 조회 (관리자)
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

2. Docker로 직접 실행
```bash
docker build -t backend-api .
docker run -p 8000:8000 --env-file .env backend-api
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 환경 변수

`.env.example` 파일을 참고하여 필요한 환경 변수를 설정하세요.

## 주의사항

- 로그인/회원가입 API는 직접 구현하지 않습니다 (Keycloak에서 처리)
- JWT 검증만 Backend에서 담당합니다
- 검색 기능은 Meilisearch와 연동됩니다

---

## Keycloak 설정 가이드

### Docker Compose로 Keycloak 시작

```bash
docker-compose up -d
```

서비스:
- **Keycloak**: http://localhost:8080 (관리자: admin/admin)
- **Meilisearch**: http://localhost:7700 (API Key: masterKey123)
- **Backend API**: http://localhost:8000

### Keycloak 초기 설정

#### 1. Realm 생성
1. http://localhost:8080 접속
2. 관리자 로그인: `admin` / `admin`
3. "Create Realm" 클릭
4. Realm name: `my-realm`
5. "Create" 클릭

#### 2. Client 생성
1. `my-realm` → `Clients` → "Create client"
2. **General settings**:
   - Client ID: `backend-client`
   - Next 클릭
3. **Capability config**:
   - Client authentication: `Off` (Public client)
   - Direct access grants: ✅ 체크 (중요!)
   - Standard flow: ✅ 체크
   - Next 클릭
4. **Login settings**:
   - Valid redirect URIs: `http://localhost:8000/*`
   - Web origins: `http://localhost:8000`
   - Save 클릭

#### 3. Realm Authentication Flow 설정 (가장 중요!)

**⚠️ 계속 오류가 발생하면 Realm을 새로 만드는 것이 가장 확실합니다!**

**방법 A: 기존 Realm 수정 (시도해볼 수 있음)**

1. `my-realm` → **"Authentication"** → **"Flows"** 탭 클릭
2. **"direct grant"** flow 찾아서 클릭
3. **"Flow: Direct Grant - Conditional OTP" 완전히 제거**:
   - "Direct Grant - Conditional OTP" 행의 **톱니바퀴 아이콘** 클릭
   - **"Delete"** 클릭 (확인 메시지에서도 Delete)
   - ⚠️ "Disabled"로 두면 안 됩니다! 완전히 삭제!
4. **"Execution: Password"** 확인:
   - **"Required"**로 설정되어 있는지 확인
5. **Save** 클릭

**방법 B: 새 Realm 생성 (가장 확실한 방법 - 권장!)**

1. `Manage realms` → **"Create realm"** 클릭
2. Realm name: `test-realm` 입력
3. **Create** 클릭
4. **Client 생성**:
   - `Clients` → "Create client"
   - Client ID: `backend-client`
   - Client authentication: `Off`
   - Direct access grants: ✅ 체크
   - Valid redirect URIs: `http://localhost:8000/*`
   - Web origins: `http://localhost:8000`
   - Save
5. **User 생성**:
   - `Users` → "Create new user"
   - Username: `testuser`
   - Email: `test@example.com`
   - Email verified: ✅ 체크
   - Enabled: ✅ 체크
   - Create
   - "Credentials" 탭에서 비밀번호 설정 (Temporary: Off)
6. **Authentication Flow 확인**:
   - `Authentication` → `Flows` → `direct grant` flow
   - "Direct Grant - Conditional OTP"가 없어야 함
   - "Execution: Password"가 "Required"인지 확인
7. **토큰 발급 테스트**:
```bash
curl -X POST "http://localhost:8080/realms/test-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-client" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testuser"
```

**⚠️ 새 Realm을 만들면 "Direct Grant - Conditional OTP" flow가 기본적으로 없을 수 있어서 문제가 해결될 수 있습니다!**

**핵심:** Password execution은 **"Required"**로 설정해야 합니다. "Alternative"로 두면 무시됩니다!

#### 4. 사용자 생성
1. `Users` → "Create new user"
2. 설정:
   - Username: `testuser`
   - Email: `test@example.com` (반드시 입력!)
   - **First name: `Test`** (중요! "Account is not fully set up" 오류 방지)
   - **Last name: `User`** (중요! "Account is not fully set up" 오류 방지)
   - Email verified: ✅ 체크
   - Enabled: ✅ 체크
   - Create 클릭
3. **"Credentials" 탭**:
   - Password: `testuser` 입력
   - Temporary: `Off`로 설정 (중요!)
   - "Set password" 클릭
4. **"Required Actions" 확인**:
   - **"Details" 탭** 클릭
   - 아래로 스크롤하여 **"Required user actions"** 섹션 찾기
   - 또는 탭 목록에서 **"Required Actions"** 탭이 있는지 확인
   - "Required user actions" 드롭다운이 있으면 모든 항목 제거
   - Save 클릭

**⚠️ 중요:** Keycloak 26.x 버전에서는 "Condition - user configured"가 First name과 Last name이 설정되어 있는지 확인합니다. 이 필드들이 비어있으면 "Account is not fully set up" 오류가 발생할 수 있습니다!

### JWT 토큰 발급

#### Public Client (권장)
```bash
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

#### Confidential Client (Client Secret 필요)
```bash
curl -X POST "http://localhost:8080/realms/my-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-client" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testuser"
```

### Backend API에서 토큰 사용

발급받은 `access_token`을 사용하여 API 호출:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/v1/users/me
```

또는 Swagger UI에서:
1. http://localhost:8000/docs 접속
2. `/api/v1/users/me` 엔드포인트 클릭
3. "Authorize" 버튼 클릭
4. 토큰 입력: `Bearer YOUR_ACCESS_TOKEN`
5. "Authorize" 후 "Try it out" 실행

### 문제 해결

#### "Account is not fully set up" 오류 (가장 흔한 문제)

**단계별 해결:**

1. **사용자 완전 삭제 후 재생성** (가장 확실한 방법):
   - `Users` → `testuser` → **Delete** 클릭
   - "Create new user" 클릭
   - Username: `testuser`
   - Email: `test@example.com` (반드시 입력!)
   - **First name: `Test`** (중요! "Account is not fully set up" 오류 방지)
   - **Last name: `User`** (중요! "Account is not fully set up" 오류 방지)
   - Email verified: ✅ 체크
   - Enabled: ✅ 체크
   - Create 클릭
   - **"Credentials" 탭**:
     - Password: `testuser` 입력
     - Password confirmation: `testuser` 입력
     - **Temporary: `Off`** (중요!)
     - "Set password" 클릭
   - **"Required Actions" 탭**:
     - 모든 항목이 비어있는지 확인
     - 체크된 항목이 있으면 모두 제거
     - Save 클릭

2. **Realm Authentication Flow 확인**:
   - `Authentication` → `Flows` → `direct grant` flow
   - "Execution: Password"가 **"Disabled"**가 아닌지 확인
   - "Alternative", "Required", 또는 "Optional"로 설정
   - "Flow: Direct Grant - Conditional OTP"는 필요없으면 제거하거나 "Disabled"로 설정

3. **사용자 계정 재확인**:
   - Email 필드에 값이 있는지 확인
   - **First name과 Last name이 설정되어 있는지 확인** (Keycloak 26.x에서 중요!)
   - Email verified: `On`
   - Enabled: `On`
   - Temporary: `Off`
   - Required Actions: 비어있음

4. **First name과 Last name 추가** (가장 빠른 해결책):
   - `Users` → `testuser` 클릭
   - **"Details" 탭**에서:
     - First name: `Test` 입력
     - Last name: `User` 입력
   - Save 클릭
   - 이렇게 하면 "Condition - user configured"가 통과됩니다!

#### "unauthorized_client" 오류
1. Client authentication: `Off` 확인 (Public client)
2. Direct access grants: ✅ 체크 확인
3. Client Secret이 있으면 제거하고 Public client로 변경

#### "invalid_client_credentials" 오류
1. Confidential client인 경우 Client Secret 확인
2. Public client로 변경하는 것을 권장

### 환경 변수 설정

`.env` 파일에 설정:
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
# Keycloak Admin Console 접근을 위한 관리자 계정 정보
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# JWT
JWT_ALGORITHM=RS256
JWT_PUBLIC_KEY=YOUR_PUBLIC_KEY  # Keycloak에서 가져오기

# Meilisearch (검색 서버)
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_API_KEY=masterKey123
```

### JWT Public Key 가져오기

```bash
curl http://localhost:8080/realms/my-realm/protocol/openid-connect/certs
```

또는 브라우저에서:
http://localhost:8080/realms/my-realm/protocol/openid-connect/certs

응답에서 공개키를 추출하여 `.env`의 `JWT_PUBLIC_KEY`에 설정합니다.

---

## 포트포워딩 가이드

### 현재 실행 환경 확인

먼저 Keycloak이 어디서 실행 중인지 확인합니다:

```bash
# Docker Compose로 실행 중인지 확인
docker-compose ps

# Kubernetes에서 실행 중인지 확인
kubectl get pods --all-namespaces | grep keycloak
```

**현재 상태:**
- ✅ **로컬 개발 환경**: Docker Compose로 Keycloak이 실행 중 (포트 8080)
- ❌ **Kubernetes 환경**: Keycloak이 배포되어 있지 않음

**로컬 개발 환경에서는 포트포워딩이 필요 없습니다!** Keycloak은 이미 `http://localhost:8080`에서 접근 가능합니다.

### Kubernetes 환경에서 Keycloak 포트포워딩 (필요한 경우)

Keycloak이 Kubernetes 클러스터에 배포되어 있는 경우에만 포트포워딩이 필요합니다.

#### 1. Keycloak 서비스 확인

```bash
# Kubernetes 클러스터 연결 확인
kubectl cluster-info

# kubeconfig 업데이트 (연결 문제가 있는 경우)
aws eks update-kubeconfig --name <cluster-name> --region <region>

# 모든 네임스페이스에서 Keycloak 서비스 찾기
kubectl get svc --all-namespaces | grep keycloak

# 또는 특정 네임스페이스에서 확인 (예: argocd 네임스페이스)
kubectl get svc -n argocd | grep keycloak
```

#### 2. 포트포워딩 실행

```bash
# 기본 포트포워딩 (로컬 8080 -> Keycloak 8080)
kubectl port-forward svc/keycloak 8080:8080 -n <namespace>

# 예시: argocd 네임스페이스에 Keycloak이 있는 경우
kubectl port-forward svc/keycloak 8080:8080 -n argocd

# 다른 로컬 포트 사용 (로컬 8081 -> Keycloak 8080)
kubectl port-forward svc/keycloak 8081:8080 -n <namespace>
```

#### 3. Pod 직접 포트포워딩

서비스가 없고 Pod에 직접 접근해야 하는 경우:

```bash
# Keycloak Pod 찾기
kubectl get pods -n <namespace> | grep keycloak

# Pod에 직접 포트포워딩
kubectl port-forward <pod-name> 8080:8080 -n <namespace>
```

#### 4. 백그라운드 실행

```bash
# 백그라운드 실행
kubectl port-forward svc/keycloak 8080:8080 -n <namespace> &

# 프로세스 ID 확인
echo $!

# 포트포워딩 중지
kill <PID>
```

### Backend API 포트포워딩

```bash
# Backend API 서비스 찾기
kubectl get svc -n formation-lap | grep backend

# 포트포워딩 (로컬 8000 -> Backend 8000)
kubectl port-forward svc/backend-service 8000:8000 -n formation-lap

# 또는 Pod 직접 접근
kubectl get pods -n formation-lap | grep backend
kubectl port-forward <backend-pod-name> 8000:8000 -n formation-lap
```

### Meilisearch 포트포워딩

```bash
# Meilisearch 서비스 찾기
kubectl get svc --all-namespaces | grep meilisearch

# 포트포워딩 (로컬 7700 -> Meilisearch 7700)
kubectl port-forward svc/meilisearch 7700:7700 -n <namespace>
```

### 접근 확인

#### 로컬 개발 환경 (Docker Compose)

```bash
# Keycloak 확인
curl http://localhost:8080

# Backend API 확인
curl http://localhost:8000/api/v1/health

# Meilisearch 확인
curl http://localhost:7700/health

# Docker Compose 서비스 상태 확인
docker-compose ps
```

#### Kubernetes 환경 (포트포워딩 후)

포트포워딩이 정상적으로 작동하는지 확인:

```bash
# Keycloak 확인
curl http://localhost:8080/health/ready

# Backend API 확인
curl http://localhost:8000/api/v1/health

# Meilisearch 확인
curl http://localhost:7700/health
```

### 문제 해결

#### Kubernetes 클러스터 연결 문제

`kubectl` 명령이 실패하는 경우:

```bash
# 1. 현재 컨텍스트 확인
kubectl config current-context

# 2. 클러스터 정보 확인
kubectl cluster-info

# 3. kubeconfig 업데이트 (EKS 클러스터인 경우)
aws eks update-kubeconfig --name <cluster-name> --region <region>

# 예시:
aws eks update-kubeconfig --name y2om-formation-lap-seoul --region ap-northeast-2

# 4. 클러스터 연결 재확인
kubectl get nodes
```

**오류 예시:**
```
dial tcp: lookup ...eks.amazonaws.com: no such host
```

**해결 방법:** kubeconfig를 최신 설정으로 업데이트합니다.

#### 포트가 이미 사용 중인 경우

```bash
# 포트 사용 중인 프로세스 확인
lsof -i :8080
# 또는
netstat -tulpn | grep 8080

# 프로세스 종료
kill <PID>

# 또는 다른 포트 사용
kubectl port-forward svc/keycloak 8081:8080 -n <namespace>
```

#### 연결이 끊어지는 경우

포트포워딩은 일시적이며 연결이 끊어질 수 있습니다. 자동 재연결 스크립트:

```bash
#!/bin/bash
# auto-port-forward.sh

while true; do
    echo "Starting port-forward..."
    kubectl port-forward svc/keycloak 8080:8080 -n <namespace>
    echo "Port-forward disconnected. Reconnecting in 5 seconds..."
    sleep 5
done
```

---

## Keycloak API 연동 확인 방법

### 1. 환경 변수 확인

`.env` 파일에 다음 변수가 설정되어 있는지 확인:

```bash
cat .env | grep KEYCLOAK
```

다음 변수들이 있어야 합니다:
- `KEYCLOAK_URL`
- `KEYCLOAK_REALM`
- `KEYCLOAK_CLIENT_ID`
- `KEYCLOAK_ADMIN_USERNAME`
- `KEYCLOAK_ADMIN_PASSWORD`

### 2. Keycloak 접근 확인

```bash
# Keycloak이 실행 중인지 확인
curl http://localhost:8080/health/ready

# 또는 브라우저에서 접근
# http://localhost:8080
```

### 3. Backend API 확인

```bash
# Backend API 헬스 체크
curl http://localhost:8000/api/v1/health

# 응답 예시: {"status":"healthy"}
```

### 4. 관리자 토큰 발급 테스트

**⚠️ 중요: master realm에 admin 사용자가 있어야 합니다!**

Keycloak Admin API를 사용하기 위해 관리자 토큰을 발급받습니다:

```bash
curl -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin"
```

**오류 발생 시 (`user_not_found` 또는 `Invalid user credentials`):**

master realm에 admin 사용자가 없을 수 있습니다. 다음 단계를 따라 생성하세요:

1. **Keycloak Admin Console 접속**
   - 브라우저에서 http://localhost:8080 접속
   - "Administration Console" 클릭
   - Username: `admin`, Password: `admin`으로 로그인

2. **master realm에 admin 사용자 생성**
   - 왼쪽 상단에서 "master" realm 선택 (이미 선택되어 있을 수 있음)
   - 왼쪽 메뉴에서 "Users" 클릭
   - "Create new user" 버튼 클릭
   - Username: `admin` 입력
   - Enabled: `ON` 체크
   - "Create" 클릭
   - "Credentials" 탭 클릭
   - Password와 Password confirmation에 `admin` 입력
   - Temporary: `OFF`로 설정 (중요!)
   - "Set password" 클릭

3. **토큰 발급 재시도**

```bash
curl -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | jq .
```

성공 시 `access_token`이 반환됩니다.

### 5. 사용자 목록 조회 테스트

관리자 토큰을 사용하여 사용자 목록을 조회합니다:

```bash
# 1. 관리자 토큰 발급
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | jq -r '.access_token')

# 2. Backend API를 통해 사용자 목록 조회
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/users?first=0&max_results=10"
```

### 6. Swagger UI에서 테스트

1. http://localhost:8000/docs 접속
2. `/api/v1/users` 엔드포인트 클릭
3. "Authorize" 버튼 클릭
4. 관리자 토큰 입력: `Bearer <admin-token>`
5. "Authorize" 후 "Try it out" 실행

### 7. 일반 사용자 토큰으로 테스트

일반 사용자 토큰으로는 본인 정보만 조회 가능:

```bash
# 1. 일반 사용자 토큰 발급
USER_TOKEN=$(curl -s -X POST "http://localhost:8080/realms/my-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-client" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testuser" | jq -r '.access_token')

# 2. 본인 정보 조회
curl -H "Authorization: Bearer $USER_TOKEN" \
  "http://localhost:8000/api/v1/users/me"

# 3. 사용자 목록 조회 시도 (관리자 권한 필요 - 실패해야 함)
curl -H "Authorization: Bearer $USER_TOKEN" \
  "http://localhost:8000/api/v1/users"
# 응답: {"detail":"Admin access required"}
```

### 8. 로그 확인

Backend API 로그에서 Keycloak API 호출 상태 확인:

```bash
# Docker Compose로 실행 중인 경우
docker-compose logs -f backend

# 또는 직접 실행 중인 경우
# 터미널에서 로그 확인
```

### 문제 해결

#### "Admin token not available" 오류

`.env` 파일에 `KEYCLOAK_ADMIN_USERNAME`과 `KEYCLOAK_ADMIN_PASSWORD`가 설정되어 있는지 확인:

```bash
grep KEYCLOAK_ADMIN .env
```

#### "Keycloak URL and Realm must be configured" 오류

`.env` 파일에 `KEYCLOAK_URL`과 `KEYCLOAK_REALM`이 설정되어 있는지 확인:

```bash
grep KEYCLOAK_URL .env
grep KEYCLOAK_REALM .env
```

#### Keycloak 연결 실패

Keycloak이 실행 중인지 확인:

```bash
# Docker Compose로 실행 중인 경우
docker-compose ps keycloak

# 포트 확인
netstat -tulpn | grep 8080

# Keycloak 로그 확인
docker-compose logs keycloak --tail=50
```

#### 관리자 토큰 발급 실패 (`user_not_found`)

**증상:**
```json
{"error": "invalid_grant", "error_description": "Invalid user credentials"}
```

**원인:** master realm에 admin 사용자가 없습니다.

**해결 방법:**
위의 "관리자 토큰 발급 테스트" 섹션을 참고하여 master realm에 admin 사용자를 생성하세요.

---

## Kubernetes 환경 설정 가이드

로컬 환경과 Kubernetes 환경의 차이점과 설정 방법을 안내합니다.

### 환경별 차이점

#### 로컬 환경 (Docker Compose)
- Keycloak: `http://localhost:8080`
- Backend API: `http://localhost:8000`
- DB: Keycloak 내장 H2 (dev-file)
- 설정: `.env` 파일 사용

#### Kubernetes 환경
- Keycloak: Kubernetes Service를 통해 접근
- Backend API: Kubernetes Service를 통해 접근
- DB: 외부 데이터베이스 (PostgreSQL 등) 또는 영구 볼륨
- 설정: ConfigMap, Secret 사용

### Kubernetes 환경 설정 단계

#### 1. Keycloak 배포

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

#### 2. Keycloak Service 생성

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

#### 3. Backend API 환경 변수 설정 (ConfigMap/Secret)

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

#### 4. 포트포워딩으로 접근

로컬에서 Kubernetes의 Keycloak에 접근하려면:

```bash
# Keycloak 포트포워딩
kubectl port-forward svc/keycloak 8080:8080 -n formation-lap

# Backend API 포트포워딩
kubectl port-forward svc/backend-service 8000:8000 -n formation-lap
```

#### 5. Keycloak 설정 (Kubernetes 환경)

포트포워딩 후 로컬과 동일하게 설정:

1. http://localhost:8080 접속 (포트포워딩 후)
2. master realm에 admin 사용자 생성
3. my-realm 생성
4. backend-client 생성
5. 테스트 사용자 생성

### Kubernetes 환경에서 JWT Public Key 가져오기

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

### Kubernetes 환경 주의사항

1. **데이터베이스**: Kubernetes 환경에서는 영구 볼륨이나 외부 DB를 사용해야 합니다
2. **비밀번호 관리**: Secret을 사용하여 민감한 정보 관리
3. **네트워크**: Service 이름으로 접근 (`http://keycloak:8080`)
4. **환경 변수**: ConfigMap과 Secret으로 분리 관리

### Kubernetes 환경 테스트 방법

#### 1. 포트포워딩 후 로컬처럼 테스트

```bash
# 포트포워딩
kubectl port-forward svc/keycloak 8080:8080 -n formation-lap &
kubectl port-forward svc/backend-service 8000:8000 -n formation-lap &

# 테스트
curl http://localhost:8000/api/v1/health
```

#### 2. Pod 내부에서 테스트

```bash
# Backend API Pod에 접속
kubectl exec -it <backend-pod-name> -n formation-lap -- bash

# Pod 내부에서 Keycloak 접근
curl http://keycloak:8080/health/ready
```

### Kubernetes 환경 문제 해결

#### Keycloak에 접근할 수 없는 경우

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

#### 환경 변수가 적용되지 않는 경우

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

---

## Keycloak 완전 설정 가이드

### 1. master realm에 admin 사용자 생성 (필수)

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

### 2. my-realm 생성

1. 왼쪽 상단의 "Add realm" 버튼 클릭
2. Realm name: `my-realm` 입력
3. "Create" 버튼 클릭

### 3. backend-client 생성 (my-realm에서)

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

### 4. 테스트 사용자 생성 (my-realm에서)

1. **Users 메뉴 클릭**: 왼쪽 메뉴에서 "Users" 클릭
2. **Create new user 클릭**: 오른쪽 상단의 "Create new user" 버튼 클릭
3. **사용자 정보 입력**:
   - Username: `testuser` 입력
   - **Email**: `test@example.com` 입력 (반드시 입력!)
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
   - "Details" 탭 클릭
   - 아래로 스크롤하여 "Required user actions" 섹션 확인
   - 모든 항목이 비어있는지 확인 (필요시 제거)
   - "Save" 버튼 클릭

**⚠️ 중요:** Email 필드는 반드시 입력해야 합니다! Email이 null이면 "Account is not fully set up" 오류가 발생합니다.

### 5. JWT Public Key 설정

`.env` 파일에 JWT Public Key를 설정합니다:

```bash
# Keycloak에서 Public Key 가져오기
python3 << 'EOF'
import json
import base64
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

response = requests.get("http://localhost:8080/realms/my-realm/protocol/openid-connect/certs")
certs = response.json()
key = certs['keys'][0]

n = int.from_bytes(base64.urlsafe_b64decode(key['n'] + '=='), 'big')
e = int.from_bytes(base64.urlsafe_b64decode(key['e'] + '=='), 'big')

pub_key = rsa.RSAPublicNumbers(e, n).public_key()
pem = pub_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

# 한 줄로 변환 (환경 변수용)
pem_one_line = pem.replace('\n', '\\n')
print(pem_one_line)
EOF
```

출력된 값을 `.env` 파일의 `JWT_PUBLIC_KEY`에 설정합니다.

### 6. 전체 테스트

#### 관리자 토큰 발급 및 사용자 목록 조회

```bash
# 1. 관리자 토큰 발급
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | jq -r '.access_token')

# 2. Backend API로 사용자 목록 조회
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/users?first=0&max_results=10"
```

#### 일반 사용자 토큰 발급 및 본인 정보 조회

```bash
# 1. 사용자 토큰 발급
USER_TOKEN=$(curl -s -X POST "http://localhost:8080/realms/my-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-client" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testuser" | jq -r '.access_token')

# 2. Backend API로 본인 정보 조회
curl -H "Authorization: Bearer $USER_TOKEN" \
  "http://localhost:8000/api/v1/users/me"

# 3. 사용자 목록 조회 시도 (관리자 권한 필요 - 실패해야 함)
curl -H "Authorization: Bearer $USER_TOKEN" \
  "http://localhost:8000/api/v1/users"
# 응답: {"detail":"Admin access required"}
```

---

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
- Authentication Flow 설정 문제

**해결 방법:**

#### 방법 1: 사용자 설정 확인 및 수정

1. **Keycloak Admin Console에서 사용자 확인**
   - my-realm → Users → testuser 클릭
   - Details 탭:
     - **Email**: 반드시 입력되어 있어야 함 (예: `test@example.com`)
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

**왜 완전히 삭제해야 하나요?**
- "Direct Grant - Conditional OTP"를 Disabled로 두면, 그 안의 "Condition - user configured"가 여전히 REQUIRED로 남아있을 수 있습니다
- 이것이 "resolve_required_actions" 오류의 원인입니다
- 완전히 삭제하면 이 문제가 해결됩니다

4. "Execution: Password" 확인:
   - "Required"로 설정되어 있는지 확인
   - "Alternative"나 "Disabled"가 아닌지 확인

#### 방법 3: 사용자 재생성 (가장 확실한 방법)

모든 설정이 올바른데도 오류가 발생한다면:

1. Users → testuser → **Delete** 클릭
2. "Create new user" 클릭
3. Username: `testuser` 입력
4. **Email**: `test@example.com` 입력 (반드시!)
5. **Email verified**: `ON`으로 설정
6. **Enabled**: `ON`으로 설정
7. "Create" 클릭
8. "Credentials" 탭:
   - Password: `testuser` 입력
   - Password confirmation: `testuser` 입력
   - **Temporary**: `OFF`로 설정 (중요!)
   - "Set password" 클릭
9. "Details" 탭:
   - "Required user actions" 섹션 확인
   - 모든 항목이 비어있는지 확인
   - Save 클릭

#### 방법 4: 다른 사용자로 테스트

testuser로 계속 문제가 발생하면 다른 사용자명으로 테스트:

1. Create new user
2. Username: `user1` (다른 이름)
3. 위의 단계를 동일하게 수행

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

### JWT Public Key 오류

**증상:**
```
JWKError: Unable to load PEM file
```

**해결 방법:**
1. `.env` 파일의 `JWT_PUBLIC_KEY` 확인
2. 위의 "JWT Public Key 설정" 섹션을 참고하여 다시 설정
3. Backend API 재시작
