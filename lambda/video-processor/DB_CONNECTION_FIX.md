# DB 연결 문제 해결

## 문제 상황

"Access denied for user 'proxy_admin'" 에러 발생

## 원인 분석

1. **사용자명/비밀번호 확인**: ✅ 일치함
   - Secrets Manager: `proxy_admin` / `test1234`
   - Lambda 환경 변수: `proxy_admin` / `test1234`

2. **가능한 원인**:
   - DB 클러스터에 `proxy_admin` 사용자가 존재하지 않음
   - DB 클러스터의 마스터 사용자와 `proxy_admin`이 다름
   - RDS Proxy를 통한 접근 권한 문제

## 해결 방법

### 옵션 1: DB에 proxy_admin 사용자 생성 (권장)

RDS 클러스터에 직접 접속하여 사용자 생성:

```sql
-- 마스터 사용자로 접속 후
CREATE USER 'proxy_admin'@'%' IDENTIFIED BY 'test1234';
GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%';
FLUSH PRIVILEGES;
```

### 옵션 2: 마스터 사용자 사용

Terraform에서 DB 클러스터의 마스터 사용자명을 확인하고, Lambda에 마스터 사용자 정보 전달

### 옵션 3: RDS Proxy IAM 인증 사용

RDS Proxy의 IAM 인증을 활성화하고 Lambda에서 IAM 역할로 인증

## 확인 사항

1. **DB 클러스터 마스터 사용자 확인**:
```bash
aws rds describe-db-clusters --db-cluster-identifier kor-aurora-mysql --query 'DBClusters[0].MasterUsername'
```

2. **DB에 사용자 존재 확인**:
```sql
SELECT User, Host FROM mysql.user WHERE User = 'proxy_admin';
```

3. **RDS Proxy 설정 확인**:
```bash
aws rds describe-db-proxies --db-proxy-name formation-lap-yuh-kor-rds-proxy
```

## 임시 해결책

DB 클러스터의 마스터 사용자 정보를 Lambda에 전달하여 사용
