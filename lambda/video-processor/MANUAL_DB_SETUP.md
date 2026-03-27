# proxy_admin 사용자 수동 생성 가이드

## 현재 상황

- **온프레미스 MySQL (Docker)**: 로컬 개발용 (`ott_mysql` 컨테이너)
- **AWS RDS Aurora MySQL**: 클라우드 프로덕션용 (`yuh-kor-aurora-mysql`)
- **문제**: Lambda 함수는 AWS RDS에 연결하려고 하는데, `proxy_admin` 사용자가 없습니다.

## ⚠️ 중요: Query Editor는 Aurora Serverless만 지원합니다

일반 Aurora MySQL은 Query Editor를 지원하지 않으므로, 아래 방법 중 하나를 사용해야 합니다.

## AWS RDS 접속 방법

### 방법 1: 온프레미스 MySQL 컨테이너 활용 (가장 간단) ⭐

온프레미스 MySQL 컨테이너(`ott_mysql`)의 MySQL 클라이언트를 사용:

**전제 조건**: RDS 보안 그룹에 본인 IP를 추가해야 합니다.

1. **RDS 보안 그룹에 본인 IP 추가**
   - AWS Console → RDS → `yuh-kor-aurora-mysql` 선택
   - "연결 및 보안" 탭 → "VPC 보안 그룹" 클릭
   - 보안 그룹 선택 → "인바운드 규칙" → "규칙 편집"
   - 규칙 추가:
     - **유형**: MySQL/Aurora
     - **포트**: 3306
     - **소스**: 내 IP (또는 본인 IP 주소 직접 입력)
     - "규칙 저장" 클릭

2. **Docker 컨테이너에서 MySQL 클라이언트 실행**
   ```bash
   # Docker 컨테이너에서 MySQL 클라이언트 실행
   docker exec -it ott_mysql mysql \
     -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
     -u admin -p \
     ott_db
   
   # 비밀번호 입력 (Terraform 변수 db_password 값)
   ```

3. **또는 한 번에 SQL 실행**
   ```bash
   docker exec -i ott_mysql mysql \
     -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
     -u admin -p'<비밀번호>' \
     ott_db \
     -e "CREATE USER IF NOT EXISTS 'proxy_admin'@'%' IDENTIFIED WITH caching_sha2_password BY 'test1234'; GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%'; FLUSH PRIVILEGES;"
   ```

### 방법 2: 로컬에서 직접 접속

로컬에 MySQL 클라이언트가 설치되어 있다면:

1. **MySQL 클라이언트 설치** (없는 경우)
   ```bash
   # Mac
   brew install mysql-client
   
   # Ubuntu/Debian
   sudo apt-get install mysql-client
   
   # Windows
   # MySQL 설치 또는 WSL 사용
   ```

2. **RDS 보안 그룹에 본인 IP 추가** (방법 1과 동일)

3. **RDS 클러스터에 접속**
   ```bash
   mysql -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
         -u admin -p \
         ott_db
   
   # 비밀번호 입력 (Terraform 변수 db_password 값)
   ```

### 방법 3: EC2 인스턴스를 통해 접속

EC2 인스턴스가 VPC 내부에 있고 RDS 보안 그룹에서 허용되어 있다면:

```bash
# EC2 인스턴스에 SSH 접속
ssh -i your-key.pem ec2-user@<ec2-ip>

# MySQL 클라이언트 설치 (없는 경우)
sudo yum install mysql -y

# RDS 클러스터에 접속
mysql -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u admin -p \
      ott_db

# 비밀번호 입력 (Terraform 변수 db_password 값)
```

## proxy_admin 사용자 생성

접속 후 다음 SQL을 실행합니다:

```sql
-- ott_db 데이터베이스 선택
USE ott_db;

-- proxy_admin 사용자 생성 (caching_sha2_password 인증 플러그인 사용)
-- RDS Proxy의 기본 인증 방식과 일치
CREATE USER IF NOT EXISTS 'proxy_admin'@'%' 
IDENTIFIED WITH caching_sha2_password BY 'test1234';

-- ott_db 데이터베이스에 대한 모든 권한 부여
GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%';

-- 권한 적용
FLUSH PRIVILEGES;

-- 사용자 확인
SELECT User, Host, plugin FROM mysql.user WHERE User = 'proxy_admin';
```

## 꼭 admin 마스터 사용자로 로그인 해야 하나요?

**답변: 네, 권장합니다.**

- **이유**: `proxy_admin` 사용자를 생성하려면 `CREATE USER` 권한이 필요합니다.
- **마스터 사용자 (`admin`)**: 모든 권한을 가지고 있어 사용자 생성이 가능합니다.
- **다른 사용자**: `CREATE USER` 권한이 있는 사용자라면 가능하지만, 일반적으로 마스터 사용자를 사용합니다.

## 사용자가 이미 존재하는 경우

만약 `proxy_admin` 사용자가 이미 존재하지만 인증 플러그인이 잘못된 경우:

```sql
-- 인증 플러그인 변경
ALTER USER 'proxy_admin'@'%' 
IDENTIFIED WITH caching_sha2_password BY 'test1234';

-- 권한 재부여
GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%';
FLUSH PRIVILEGES;
```

## 확인

```sql
-- 사용자 목록 확인
SELECT User, Host, plugin FROM mysql.user WHERE User IN ('admin', 'proxy_admin');

-- 권한 확인
SHOW GRANTS FOR 'proxy_admin'@'%';

-- 테이블 확인
SHOW TABLES;
```

## Secrets Manager 정보

현재 Secrets Manager에 저장된 정보:

```json
{
    "username": "proxy_admin",
    "password": "test1234",
    "engine": "mysql",
    "host": "kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com",
    "port": 3306,
    "dbname": "ott_db"
}
```

## RDS Proxy 설정 확인

현재 RDS Proxy는 다음 Secrets Manager를 사용합니다:
- **Secret ARN**: `formation-lap/db/dev/credentials`
- **사용자명**: `proxy_admin`
- **비밀번호**: `test1234`
- **RDS Proxy 엔드포인트**: `formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com`

RDS Proxy는 Secrets Manager에 등록된 사용자만 허용하므로, 위 정보와 일치하는 사용자가 DB에 존재해야 합니다.

## 참고

- **인증 플러그인**: RDS Proxy는 `mysql_native_password` 또는 `caching_sha2_password`만 지원합니다.
- **비밀번호**: Secrets Manager에 저장된 비밀번호와 일치해야 합니다 (`test1234`).
- **호스트**: `%`는 모든 호스트에서 접속을 허용합니다.
- **데이터베이스**: `ott_db`에 대한 모든 권한이 필요합니다.

## 완료 후

사용자 생성이 완료되면 Lambda 함수가 자동으로 `proxy_admin` 사용자로 RDS Proxy를 통해 연결하여 영상 메타데이터를 DB에 등록합니다.

## 테스트

사용자 생성 후 다음 명령으로 테스트할 수 있습니다:

```bash
# RDS Proxy를 통해 연결 테스트 (Docker 컨테이너 사용)
docker exec -it ott_mysql mysql \
  -h formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
  -u proxy_admin -p \
  ott_db

# 비밀번호: test1234
```

## 온프레미스 MySQL과의 차이

- **온프레미스 MySQL (Docker)**: 로컬 개발용, `docker exec -it ott_mysql mysql -u root -p`
- **AWS RDS Aurora MySQL**: 클라우드 프로덕션용, 위 방법으로 접속

**주의**: 두 데이터베이스는 완전히 별개입니다. 온프레미스 MySQL에 사용자를 생성해도 AWS RDS에는 영향을 주지 않습니다.
