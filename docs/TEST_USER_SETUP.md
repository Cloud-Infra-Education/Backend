# Keycloak 테스트 사용자 설정 가이드

"Account is not fully set up" 오류 해결 방법

## 문제 원인

Keycloak 사용자 계정에 Required Actions가 설정되어 있거나, 필수 정보가 누락된 경우 발생합니다.

## 해결 방법

### 1. 사용자 상세 정보 확인

1. Keycloak Admin Console 접속: http://localhost:8080
2. my-realm 선택
3. Users → testuser 클릭

### 2. Details 탭 확인 및 수정

다음 항목들을 확인하고 수정:

- **Username**: `testuser` (이미 설정됨)
- **Email**: `test@example.com` (반드시 입력!)
- **Email verified**: `ON`으로 설정
- **Enabled**: `ON`으로 설정
- **First name**: (선택사항)
- **Last name**: (선택사항)

**Save** 버튼 클릭

### 3. Required Actions 탭 확인

1. "Required Actions" 탭 클릭
2. 모든 항목이 비어있는지 확인
3. 체크된 항목이 있으면 모두 제거
4. **Save** 버튼 클릭

### 4. Credentials 탭 확인

1. "Credentials" 탭 클릭
2. 비밀번호가 설정되어 있는지 확인
3. **Temporary**: `OFF`로 설정되어 있어야 함
4. Temporary가 ON이면:
   - Password 입력
   - Password confirmation 입력
   - **Temporary**: `OFF`로 변경
   - "Set password" 클릭

### 5. 테스트

설정 완료 후 토큰 발급 테스트:

```bash
curl -X POST "http://localhost:8080/realms/my-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-client" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testuser" | jq .
```

성공 시 `access_token`이 반환됩니다.

## 체크리스트

- [ ] Email 필드에 값이 입력되어 있음
- [ ] Email verified: ON
- [ ] Enabled: ON
- [ ] Required Actions: 비어있음
- [ ] Credentials: 비밀번호 설정됨
- [ ] Temporary: OFF

## 추가 문제 해결

### "resolve_required_actions" 오류

Realm의 Authentication Flow를 확인:

1. my-realm → Authentication → Flows
2. "direct grant" flow 선택
3. "Direct Grant - Conditional OTP" 제거 (있는 경우)
4. "Execution: Password"가 "Required"로 설정되어 있는지 확인

### 사용자 재생성 (최후의 수단)

위 방법이 모두 실패하면 사용자를 삭제하고 재생성:

1. Users → testuser → Delete
2. Create new user
3. 위의 단계를 다시 수행
