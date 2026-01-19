#!/bin/bash
# 회원가입 + Keycloak 동기화 스크립트
# 사용법: ./sync_user_to_keycloak.sh <email> <password>

set -e

if [ $# -lt 2 ]; then
    echo "사용법: $0 <email> <password> [first_name] [last_name]"
    exit 1
fi

EMAIL="$1"
PASSWORD="$2"
FIRST_NAME="${3:-User}"
LAST_NAME="${4:-Member}"

API_URL="https://api.exampleott.click"
KEYCLOAK_URL="https://api.exampleott.click/keycloak"
REALM="formation-lap"

echo "=== 회원가입 + Keycloak 동기화 ==="
echo "이메일: $EMAIL"
echo ""

# 1. 회원가입 (DB에 저장)
echo "1. 회원가입 (DB)..."
REGISTER_RESULT=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\",
    \"region_code\": \"KR\",
    \"subscription_status\": \"free\",
    \"first_name\": \"$FIRST_NAME\",
    \"last_name\": \"$LAST_NAME\"
  }")

echo "$REGISTER_RESULT" | jq '.'

# 회원가입 실패 시 종료
if echo "$REGISTER_RESULT" | jq -e '.detail' > /dev/null 2>&1; then
    echo "❌ 회원가입 실패"
    exit 1
fi

# 2. Keycloak Admin 토큰 발급
echo ""
echo "2. Keycloak 사용자 생성..."
TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | jq -r '.access_token')

# 3. Keycloak에 사용자 생성
KC_RESULT=$(curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$EMAIL\",
    \"email\": \"$EMAIL\",
    \"enabled\": true,
    \"emailVerified\": true,
    \"firstName\": \"$FIRST_NAME\",
    \"lastName\": \"$LAST_NAME\",
    \"credentials\": [{
      \"type\": \"password\",
      \"value\": \"$PASSWORD\",
      \"temporary\": false
    }]
  }" -w "%{http_code}" -o /dev/null)

if [ "$KC_RESULT" = "201" ]; then
    echo "✅ Keycloak 사용자 생성 완료"
elif [ "$KC_RESULT" = "409" ]; then
    echo "⚠️  Keycloak에 이미 존재하는 사용자"
else
    echo "❌ Keycloak 사용자 생성 실패 (HTTP $KC_RESULT)"
fi

# 4. 로그인 테스트
echo ""
echo "3. 로그인 테스트..."
LOGIN_RESULT=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

if echo "$LOGIN_RESULT" | jq -e '.access_token' > /dev/null 2>&1; then
    echo "✅ 로그인 성공!"
    echo "$LOGIN_RESULT" | jq '{token_type, expires_in}'
else
    echo "❌ 로그인 실패"
    echo "$LOGIN_RESULT" | jq '.'
fi
