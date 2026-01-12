#!/bin/bash
# Bastion 인스턴스에서 실행할 데이터베이스 설정 스크립트
# 이 스크립트는 Bastion 인스턴스에 업로드한 후 실행해야 합니다

# RDS 클러스터 엔드포인트
DB_HOST="y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com"
DB_USER="admin"
DB_PASSWORD="StrongPassword123!"

# Secrets Manager에 저장된 값
PROXY_USER="proxy_admin"
PROXY_PASSWORD="test1234"
DB_NAME="ott_db"

echo "=========================================="
echo "데이터베이스 설정 스크립트"
echo "=========================================="
echo "RDS 클러스터: $DB_HOST"
echo "마스터 사용자: $DB_USER"
echo "생성할 데이터베이스: $DB_NAME"
echo "생성할 사용자: $PROXY_USER"
echo ""

# MySQL 클라이언트 설치 확인
if ! command -v mysql &> /dev/null; then
    echo "📦 MySQL 클라이언트 설치 중..."
    sudo yum update -y
    # Amazon Linux 2023에서는 mariadb105 사용
    sudo yum install -y mariadb105 || sudo yum install -y mariadb || sudo yum install -y mysql80
fi

echo "🔌 RDS 클러스터에 연결 중..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" << EOF

-- 현재 데이터베이스 목록 확인
SHOW DATABASES;

-- ott_db 데이터베이스가 없으면 생성
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- proxy_admin 사용자가 없으면 생성
CREATE USER IF NOT EXISTS '${PROXY_USER}'@'%' IDENTIFIED BY '${PROXY_PASSWORD}';

-- ott_db에 대한 권한 부여
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${PROXY_USER}'@'%';

-- 권한 새로고침
FLUSH PRIVILEGES;

-- 생성된 사용자 확인
SELECT User, Host FROM mysql.user WHERE User = '${PROXY_USER}';

-- 데이터베이스 목록 다시 확인
SHOW DATABASES;

-- ott_db로 전환
USE ${DB_NAME};

-- users 테이블이 없으면 생성
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    last_region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 테이블 확인
SHOW TABLES;

-- 현재 상태 확인
SELECT 'Database and user setup completed!' AS Status;

EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 데이터베이스 설정 완료!"
    echo "  - 데이터베이스: $DB_NAME"
    echo "  - 사용자: $PROXY_USER"
    echo "  - 테이블: users"
else
    echo ""
    echo "❌ 데이터베이스 설정 실패"
    exit 1
fi
