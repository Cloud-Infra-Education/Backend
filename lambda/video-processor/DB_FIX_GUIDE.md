# DB 연결 문제 해결 가이드

## 문제

"Access denied for user 'proxy_admin'" 에러 발생

## 원인

- DB 클러스터의 마스터 사용자: `admin`
- Lambda가 사용하는 사용자: `proxy_admin` (Secrets Manager에서 가져옴)
- DB에 `proxy_admin` 사용자가 존재하지 않음

## 해결 방법

### 방법 1: DB에 proxy_admin 사용자 생성 (권장)

RDS 클러스터에 마스터 사용자(`admin`)로 접속하여 `proxy_admin` 사용자를 생성:

```sql
-- RDS 클러스터 엔드포인트로 접속 (마스터 사용자: admin)
mysql -h yuh-kor-aurora-mysql.cluster-xxxxx.ap-northeast-2.rds.amazonaws.com -u admin -p

-- 또는 RDS Proxy를 통해 접속
mysql -h formation-lap-yuh-kor-rds-proxy.proxy-xxxxx.ap-northeast-2.rds.amazonaws.com -u admin -p
```

접속 후:

```sql
-- proxy_admin 사용자 생성
CREATE USER IF NOT EXISTS 'proxy_admin'@'%' IDENTIFIED BY 'test1234';

-- ott_db 데이터베이스에 대한 모든 권한 부여
GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%';

-- 권한 적용
FLUSH PRIVILEGES;

-- 사용자 확인
SELECT User, Host FROM mysql.user WHERE User = 'proxy_admin';
```

### 방법 2: Lambda에서 마스터 사용자(admin) 사용

Terraform을 수정하여 Lambda에 마스터 사용자 정보 전달:

```hcl
# main.tf에서
db_username = var.db_username  # admin
db_password = var.db_password  # 마스터 비밀번호
```

하지만 이 경우 Secrets Manager와 불일치하므로 권장하지 않습니다.

## 확인 방법

### 1. DB 사용자 목록 확인

```sql
SELECT User, Host FROM mysql.user;
```

### 2. proxy_admin 사용자 권한 확인

```sql
SHOW GRANTS FOR 'proxy_admin'@'%';
```

### 3. Lambda 환경 변수 확인

```bash
aws lambda get-function-configuration \
  --function-name formation-lap-video-processor \
  --query 'Environment.Variables'
```

## 예상 결과

사용자 생성 후:
- Lambda 함수가 `proxy_admin`으로 DB에 접근 가능
- `contents` 및 `video_assets` 테이블에 데이터 저장 성공
