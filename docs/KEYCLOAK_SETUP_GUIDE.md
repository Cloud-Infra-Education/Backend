# Keycloak 설정 가이드

## 1. master realm에 admin 사용자 생성 (필수)

Backend API에서 Keycloak Admin API를 사용하려면 master realm에 admin 사용자가 필요합니다.

### 단계:

1. **현재 위치 확인**: 왼쪽 상단에서 "master" realm이 선택되어 있는지 확인
2. **Users 메뉴 클릭**: 왼쪽 메뉴에서 "Users" 클릭
3. **Create new user 클릭**: 오른쪽 상단의 "Create new user" 버튼 클릭
4. **사용자 정보 입력**:
   - Username: `admin` 입력
   - Email: `admin@example.com` (선택사항)
   - First name: `Admin` (선택사항)
   - Last name: `User` (선택사항)
   - **Enabled**: `ON`으로 설정 (중요!)
   - "Create" 버튼 클릭
5. **비밀번호 설정**:
   - "Credentials" 탭 클릭
   - Password: `admin` 입력
   - Password confirmation: `admin` 입력
   - **Temporary**: `OFF`로 설정 (중요! 임시 비밀번호가 아니도록)
   - "Set password" 버튼 클릭

## 2. my-realm 확인 및 생성

애플리케이션에서 사용할 realm을 확인하거나 생성합니다.

### my-realm이 이미 있는 경우:

1. 왼쪽 상단의 "master" 옆에 있는 드롭다운 클릭
2. "my-realm" 선택
3. 이미 설정되어 있으면 다음 단계로 진행

### my-realm이 없는 경우:

1. 왼쪽 상단의 "Add realm" 버튼 클릭
2. Realm name: `my-realm` 입력
3. "Create" 버튼 클릭

## 3. backend-client 생성 (my-realm에서)

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

## 4. 테스트 사용자 생성 (my-realm에서)

1. **Users 메뉴 클릭**: 왼쪽 메뉴에서 "Users" 클릭
2. **Create new user 클릭**: 오른쪽 상단의 "Create new user" 버튼 클릭
3. **사용자 정보 입력**:
   - Username: `testuser` 입력
   - Email: `test@example.com` 입력
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

## 5. 설정 확인

### master realm admin 사용자 확인:

```bash
curl -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | jq .
```

### my-realm 테스트 사용자 토큰 발급:

```bash
curl -X POST "http://localhost:8080/realms/my-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-client" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testuser" | jq .
```

## 6. Backend API 테스트

### 관리자 토큰으로 사용자 목록 조회:

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

### 일반 사용자로 본인 정보 조회:

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
```

## 문제 해결

### "Account is not fully set up" 오류

- 사용자의 "Required Actions" 탭에서 모든 항목 제거
- Email verified: ON 확인
- Temporary: OFF 확인

### "user_not_found" 오류

- master realm에 admin 사용자가 생성되었는지 확인
- Username이 정확한지 확인

### 토큰 발급 실패

- Client의 "Direct access grants"가 ON인지 확인
- Realm의 Authentication Flow에서 "Direct Grant - Conditional OTP" 제거 확인
