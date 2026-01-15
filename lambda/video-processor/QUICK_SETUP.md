# 빠른 설정 가이드

## 현재 상황
✅ Lambda 함수가 RDS Proxy에 연결되어 있음 (확인 완료)
❌ `proxy_admin` 사용자가 DB에 없음 (생성 필요)

## 다음 단계

### 1. RDS 보안 그룹에 본인 IP 추가

**보안 그룹 ID**: `sg-000e62dee81be9710`

**방법 1: AWS Console 사용**
1. AWS Console → EC2 → 보안 그룹
2. 보안 그룹 ID `sg-000e62dee81be9710` 검색
3. "인바운드 규칙" → "규칙 편집"
4. 규칙 추가:
   - **유형**: MySQL/Aurora
   - **포트**: 3306
   - **소스**: 내 IP (또는 본인 IP 주소 직접 입력)
   - "규칙 저장"

**방법 2: AWS CLI 사용**
```bash
# 본인 IP 확인
MY_IP=$(curl -s https://checkip.amazonaws.com)

# 보안 그룹에 규칙 추가
aws ec2 authorize-security-group-ingress \
  --group-id sg-000e62dee81be9710 \
  --protocol tcp \
  --port 3306 \
  --cidr ${MY_IP}/32 \
  --region ap-northeast-2
```

### 2. Docker 컨테이너로 RDS 접속

```bash
# Docker 컨테이너에서 MySQL 클라이언트 실행
docker exec -it ott_mysql mysql \
  -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
  -u admin -p \
  ott_db

# 비밀번호 입력 (Terraform 변수 db_password 값)
```

### 3. 사용자 생성 SQL 실행

접속 후 다음 SQL 실행:

```sql
USE ott_db;

CREATE USER IF NOT EXISTS 'proxy_admin'@'%' 
IDENTIFIED WITH caching_sha2_password BY 'test1234';

GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%';
FLUSH PRIVILEGES;

SELECT User, Host, plugin FROM mysql.user WHERE User = 'proxy_admin';
```

### 또는 한 번에 실행

```bash
# 비밀번호를 환경 변수로 설정 (선택사항)
export DB_PASSWORD="<Terraform 변수 db_password 값>"

# 한 번에 실행
docker exec -i ott_mysql mysql \
  -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
  -u admin -p"${DB_PASSWORD}" \
  ott_db \
  -e "USE ott_db; CREATE USER IF NOT EXISTS 'proxy_admin'@'%' IDENTIFIED WITH caching_sha2_password BY 'test1234'; GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%'; FLUSH PRIVILEGES; SELECT User, Host, plugin FROM mysql.user WHERE User = 'proxy_admin';"
```

## 확인

사용자 생성 후 Lambda 함수가 자동으로 연결됩니다. S3에 영상을 업로드하여 테스트하세요!
