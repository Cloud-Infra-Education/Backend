# Bastion 인스턴스를 통한 데이터베이스 설정 가이드

## 현재 상황

- **RDS 클러스터 엔드포인트**: `y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com`
- **RDS 마스터 사용자**: `admin` / `StrongPassword123!`
- **Secrets Manager 저장 값**: `proxy_admin` / `test1234` / `ott_db`
- **Bastion 인스턴스**: `ec2-43-202-55-63.ap-northeast-2.compute.amazonaws.com`

## 문제점

현재 RDS 클러스터 보안 그룹이 RDS Proxy 보안 그룹만 허용하도록 설정되어 있어, Bastion에서 직접 RDS 클러스터에 연결할 수 없을 수 있습니다.

## 해결 방법

### 방법 1: 보안 그룹 규칙 추가 (권장)

Bastion 인스턴스의 보안 그룹 ID를 RDS 클러스터 보안 그룹에 추가해야 합니다.

Bastion 보안 그룹 ID: `sg-01c70dc0fd061f8ed`

Terraform 코드에 다음 규칙을 추가해야 합니다:
- `Terraform/modules/database/security-group.tf`에 Bastion → RDS 클러스터 규칙 추가

### 방법 2: 직접 연결 시도

먼저 연결을 시도해보고, 실패하면 방법 1을 사용하세요.

## 실행 방법

### 1단계: Bastion에 SSH 연결

```bash
cd /root/Backend
./connect-to-bastion.sh
```

### 2단계: 데이터베이스 설정 스크립트 업로드 및 실행

로컬에서 실행:
```bash
cd /root/Backend
./upload-and-run-db-setup.sh
```

또는 Bastion에 직접 SSH로 들어가서:
```bash
# MySQL 클라이언트 설치
sudo yum install -y mysql

# RDS 클러스터에 연결
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u admin -p'StrongPassword123!'
```

### 3단계: 데이터베이스 및 사용자 생성

MySQL 프롬프트에서:
```sql
-- ott_db 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS ott_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- proxy_admin 사용자 생성
CREATE USER IF NOT EXISTS 'proxy_admin'@'%' IDENTIFIED BY 'test1234';

-- ott_db에 대한 권한 부여
GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%';

-- 권한 새로고침
FLUSH PRIVILEGES;

-- 확인
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User = 'proxy_admin';
USE ott_db;

-- users 테이블 생성 (필요한 경우)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    last_region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SHOW TABLES;
```

## 확인 사항

1. `ott_db` 데이터베이스가 생성되었는지 확인
2. `proxy_admin` 사용자가 생성되었는지 확인
3. `proxy_admin` 사용자가 `ott_db`에 대한 권한을 가지고 있는지 확인
4. `users` 테이블이 생성되었는지 확인

## 다음 단계

데이터베이스 설정이 완료되면:
1. Kubernetes Pod에서 DB 연결 테스트
2. API 엔드포인트 테스트 (/register 등)
