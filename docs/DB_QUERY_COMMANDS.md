# 데이터베이스 조회 명령어 모음

## 📌 기본 연결 명령어

```bash
# RDS 클러스터에 연결
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' ott_db

# 또는 마스터 사용자로 연결
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u admin -p'StrongPassword123!'
```

## 🔍 데이터베이스 조회 명령어

### 1. 데이터베이스 목록 확인
```sql
SHOW DATABASES;
```

### 2. 현재 데이터베이스 선택
```sql
USE ott_db;
```

### 3. 테이블 목록 확인
```sql
-- ott_db 데이터베이스의 테이블 목록
SHOW TABLES;

-- 또는 다른 데이터베이스의 테이블 목록
SHOW TABLES FROM ott_db;
```

### 4. 테이블 구조 확인
```sql
-- users 테이블의 구조 확인
DESCRIBE users;
-- 또는
DESC users;
-- 또는
SHOW CREATE TABLE users;
```

### 5. 데이터 조회
```sql
-- users 테이블의 모든 데이터 조회
SELECT * FROM users;

-- 특정 조건으로 조회
SELECT * FROM users WHERE email = 'test@example.com';

-- 개수 확인
SELECT COUNT(*) as total_users FROM users;

-- 처음 10개만 조회
SELECT * FROM users LIMIT 10;

-- 정렬하여 조회
SELECT * FROM users ORDER BY created_at DESC;

-- 특정 컬럼만 조회
SELECT id, email, last_region, created_at FROM users;
```

### 6. 사용자 정보 확인
```sql
-- 현재 사용자 확인
SELECT USER(), CURRENT_USER();

-- 모든 사용자 목록 확인
SELECT User, Host FROM mysql.user;

-- proxy_admin 사용자 권한 확인
SHOW GRANTS FOR 'proxy_admin'@'%';
```

### 7. 데이터베이스 정보 확인
```sql
-- 현재 데이터베이스 확인
SELECT DATABASE();

-- 테이블 상태 확인
SHOW TABLE STATUS FROM ott_db;
```

## 🚀 한 줄 명령어 (Bastion에서 직접 실행)

```bash
# 데이터베이스 목록 확인
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' -e "SHOW DATABASES;"

# ott_db의 테이블 목록 확인
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' ott_db -e "SHOW TABLES;"

# users 테이블의 모든 데이터 조회
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' ott_db -e "SELECT * FROM users;"

# users 테이블 구조 확인
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' ott_db -e "DESCRIBE users;"

# users 테이블 레코드 개수 확인
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' ott_db -e "SELECT COUNT(*) as total FROM users;"

# 사용자 정보 확인
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' -e "SELECT User, Host FROM mysql.user WHERE User = 'proxy_admin';"
```

## 📊 유용한 조회 쿼리 예제

```sql
-- users 테이블의 최근 가입자 5명
SELECT * FROM users ORDER BY created_at DESC LIMIT 5;

-- 지역별 사용자 수
SELECT last_region, COUNT(*) as count FROM users GROUP BY last_region;

-- 오늘 가입한 사용자
SELECT * FROM users WHERE DATE(created_at) = CURDATE();

-- 이메일 도메인별 사용자 수
SELECT SUBSTRING_INDEX(email, '@', -1) as domain, COUNT(*) as count 
FROM users 
GROUP BY domain;
```
