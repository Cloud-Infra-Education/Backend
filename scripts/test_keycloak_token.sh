#!/bin/bash

# Keycloak 토큰 발급 테스트 스크립트

REALM="my-realm"
CLIENT_ID="backend-client"
USERNAME="testuser"
PASSWORD="testuser"
KEYCLOAK_URL="http://localhost:8080"

echo "=== Keycloak 토큰 발급 테스트 ==="
echo "Realm: $REALM"
echo "Client ID: $CLIENT_ID"
echo "Username: $USERNAME"
echo ""

# Public client로 테스트 (client_secret 없이)
echo "1. Public Client로 테스트 (client_secret 없이)..."
RESPONSE=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$CLIENT_ID" \
  -d "grant_type=password" \
  -d "username=$USERNAME" \
  -d "password=$PASSWORD")

echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Realm 정보 확인
echo "2. Realm 설정 확인..."
curl -s "$KEYCLOAK_URL/realms/$REALM/.well-known/openid-configuration" | python3 -c "import sys, json; d=json.load(sys.stdin); print('Token endpoint:', d.get('token_endpoint')); print('Realm:', d.get('issuer'))" 2>/dev/null || echo "Realm 확인 실패"
echo ""
