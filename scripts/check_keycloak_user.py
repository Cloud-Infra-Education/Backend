#!/usr/bin/env python3
"""
Keycloak 사용자 및 클라이언트 설정 확인 스크립트
"""
import requests
import json

KEYCLOAK_URL = "http://localhost:8080"
REALM = "my-realm"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"

def get_admin_token():
    """관리자 토큰 발급"""
    url = f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"
    data = {
        "client_id": "admin-cli",
        "username": ADMIN_USER,
        "password": ADMIN_PASSWORD,
        "grant_type": "password"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def check_user(token, username):
    """사용자 정보 확인"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"username": username, "exact": "true"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        users = response.json()
        if users:
            return users[0]
    return None

def check_client(token, client_id):
    """클라이언트 정보 확인"""
    url = f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"clientId": client_id}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        clients = response.json()
        if clients:
            return clients[0]
    return None

def main():
    print("=== Keycloak 설정 확인 ===\n")
    
    # 관리자 토큰 발급
    print("1. 관리자 토큰 발급 중...")
    token = get_admin_token()
    if not token:
        print("❌ 관리자 토큰 발급 실패")
        return
    print("✅ 관리자 토큰 발급 성공\n")
    
    # 사용자 확인
    print("2. 사용자 정보 확인 중...")
    user = check_user(token, "testuser")
    if user:
        print(f"✅ 사용자 발견: {user['username']}")
        print(f"   - ID: {user['id']}")
        print(f"   - Email: {user.get('email', 'N/A')}")
        print(f"   - Email verified: {user.get('emailVerified', False)}")
        print(f"   - Enabled: {user.get('enabled', False)}")
        
        # Required Actions 확인
        required_actions = user.get('requiredActions', [])
        if required_actions:
            print(f"   ⚠️  Required Actions: {required_actions}")
        else:
            print(f"   ✅ Required Actions: 없음")
    else:
        print("❌ 사용자를 찾을 수 없습니다")
    
    print()
    
    # 클라이언트 확인
    print("3. 클라이언트 정보 확인 중...")
    client = check_client(token, "backend-client")
    if client:
        print(f"✅ 클라이언트 발견: {client['clientId']}")
        print(f"   - ID: {client['id']}")
        print(f"   - Client authentication: {client.get('publicClient', False) == False}")
        print(f"   - Public client: {client.get('publicClient', False)}")
        print(f"   - Direct access grants: {client.get('directAccessGrantsEnabled', False)}")
        print(f"   - Standard flow: {client.get('standardFlowEnabled', False)}")
    else:
        print("❌ 클라이언트를 찾을 수 없습니다")
    
    print("\n=== 확인 완료 ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
