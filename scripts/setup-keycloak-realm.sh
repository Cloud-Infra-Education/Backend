#!/bin/bash
# Keycloak realm 설정 스크립트

echo "=== Keycloak Realm 설정 ==="
echo ""

# 관리자 토큰 발급
echo "1. 관리자 토큰 발급 중..."
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ 관리자 토큰 발급 실패"
  exit 1
fi

echo "✅ 관리자 토큰 발급 성공"
echo ""

# my-realm 존재 확인
echo "2. my-realm 존재 확인 중..."
REALM_EXISTS=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8080/admin/realms/my-realm" | jq -r '.realm' 2>/dev/null)

if [ "$REALM_EXISTS" == "my-realm" ]; then
  echo "✅ my-realm이 이미 존재합니다"
else
  echo "my-realm이 없습니다. Admin Console에서 수동으로 생성해주세요."
  echo "http://localhost:8080 → Add realm → my-realm"
  exit 1
fi

echo ""
echo "=== 설정 완료 ==="
echo "my-realm이 준비되었습니다."
