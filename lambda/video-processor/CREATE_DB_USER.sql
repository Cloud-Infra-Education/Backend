-- DB에 proxy_admin 사용자 생성 스크립트
-- 마스터 사용자(admin)로 DB에 접속하여 실행

-- 1. proxy_admin 사용자 생성
CREATE USER IF NOT EXISTS 'proxy_admin'@'%' IDENTIFIED BY 'test1234';

-- 2. ott_db 데이터베이스에 대한 모든 권한 부여
GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%';

-- 3. 권한 적용
FLUSH PRIVILEGES;

-- 4. 사용자 확인
SELECT User, Host FROM mysql.user WHERE User = 'proxy_admin';
