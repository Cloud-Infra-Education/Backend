# API 테스트 가이드

## 📊 현재 진행 상황

### ✅ 완료된 작업
1. **Terraform Outputs 활성화** - RDS Proxy 엔드포인트를 변수로 관리
2. **.env 파일 업데이트** - RDS Proxy 엔드포인트로 변경 완료
3. **자동 업데이트 스크립트 생성** - `update_db_endpoint.sh` 스크립트 생성
4. **서버 실행 중** - 포트 8001에서 FastAPI 서버 실행 중

### ⚠️ 현재 문제점
- **DB 연결 실패**: RDS Proxy에 연결할 수 없음
- **원인 추정**: 네트워크/보안 그룹 설정 문제
  - RDS Proxy는 VPC 내부에서만 접근 가능
  - 현재 서버가 VPC 내부에 있지 않거나 보안 그룹이 차단 중일 수 있음

## 🧪 테스트 방법

### 1. 서버 상태 확인
```bash
# 서버가 실행 중인지 확인
ps aux | grep uvicorn

# 서버 응답 확인
curl http://localhost:8001/
```

### 2. API 엔드포인트 테스트

#### 브라우저에서 테스트 (Swagger UI)
```
http://192.168.137.128:8001/docs
```

#### curl로 테스트
```bash
# 회원가입 API 테스트
curl -X POST "http://localhost:8001/users/users/register" \
  -H "Content-Type: application/json" \
  -H "x-region: seoul" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'

# 로그인 API 테스트
curl -X POST "http://localhost:8001/users/users/login" \
  -H "Content-Type: application/json" \
  -H "x-region: seoul" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'
```

### 3. DB 연결 테스트
```bash
cd /root/Backend
python3 -c "from users.database import get_db_conn; import asyncio; asyncio.run(get_db_conn())"
```

## 🔧 다음 단계 (DB 연결 문제 해결)

### 옵션 1: 네트워크/보안 그룹 확인
```bash
# Terraform 보안 그룹 설정 확인
cd /root/Terraform/modules/database
cat security-group.tf

# 현재 서버의 IP/보안 그룹이 RDS Proxy 보안 그룹에 허용되어 있는지 확인
```

### 옵션 2: 서버를 VPC 내부로 이동
- EKS 클러스터 내부에서 실행
- 또는 VPC 내부의 EC2 인스턴스에서 실행

### 옵션 3: 로컬 개발 환경 사용
- RDS Proxy 대신 로컬 DB 사용 (test.db)
- 또는 VPN/Bastion Host를 통해 접근

## 📝 유용한 명령어

### 환경 변수 확인
```bash
cd /root/Backend
cat .env
```

### DB 엔드포인트 업데이트 (Terraform 변경 후)
```bash
cd /root/Backend
./update_db_endpoint.sh
```

### 서버 재시작
```bash
# 현재 서버 중지
pkill -f "uvicorn main:app"

# 서버 시작
cd /root/Backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### 서버 로그 확인
```bash
# 서버 실행 중인 경우 로그를 확인하려면
# 서버를 포그라운드에서 실행하거나
# 로그 파일을 확인하세요
```
