# AWS RDS에 proxy_admin 사용자 생성 가이드

## 문제 상황

Lambda 함수가 `proxy_admin` 사용자로 AWS RDS에 접근하려 하지만, 해당 사용자가 존재하지 않아 "Access denied" 에러 발생

## 해결 방법

### 방법 1: RDS 클러스터 엔드포인트에 직접 접속 (권장)

**1단계: RDS 클러스터 엔드포인트 확인**
```bash
aws rds describe-db-clusters \
  --db-cluster-identifier yuh-kor-aurora-mysql \
  --region ap-northeast-2 \
  --query 'DBClusters[0].Endpoint' \
  --output text
```

**2단계: 마스터 사용자(admin)로 접속**
```bash
mysql -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u admin -p \
      ott_db
```

**3단계: proxy_admin 사용자 생성**
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

### 방법 2: RDS Proxy를 통해 접속

RDS Proxy 엔드포인트를 통해 접속할 수도 있지만, 마스터 사용자로 접속 가능한지 확인이 필요합니다.

### 방법 3: AWS Systems Manager Session Manager 사용

Bastion Host나 EC2 인스턴스를 통해 접속:

```bash
# EC2 인스턴스에 접속 후
mysql -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u admin -p \
      ott_db
```

## 확인 사항

### 1. Secrets Manager 확인
```bash
aws secretsmanager get-secret-value \
  --secret-id formation-lap/db/dev/credentials \
  --region ap-northeast-2 \
  --query 'SecretString' \
  --output text
```

예상 결과:
```json
{
  "username": "proxy_admin",
  "password": "test1234",
  ...
}
```

### 2. Lambda 환경 변수 확인
```bash
aws lambda get-function-configuration \
  --function-name formation-lap-video-processor \
  --region ap-northeast-2 \
  --query 'Environment.Variables'
```

예상 결과:
```json
{
  "DB_USER": "proxy_admin",
  "DB_PASSWORD": "test1234",
  "DB_HOST": "formation-lap-yuh-kor-rds-proxy.proxy-xxxxx.ap-northeast-2.rds.amazonaws.com",
  "DB_NAME": "ott_db"
}
```

### 3. 사용자 생성 후 테스트

S3에 영상을 업로드하여 Lambda 함수가 정상적으로 DB에 데이터를 저장하는지 확인:

```bash
# S3에 영상 업로드
aws s3 cp test_video.mp4 s3://team-formation-lap-origin-s3/videos/1_test_video.mp4

# Lambda 로그 확인
aws logs tail /aws/lambda/formation-lap-video-processor --follow
```

## 온프레미스 vs AWS RDS

| 항목 | 온프레미스 MySQL | AWS RDS Aurora MySQL |
|------|-----------------|---------------------|
| 마스터 사용자 | `root` | `admin` |
| Lambda 사용자 | 불필요 (로컬) | `proxy_admin` (필수) |
| 사용자 생성 | 선택사항 | **필수** |

## 참고

- 온프레미스 MySQL의 `init.sql`에 사용자 생성 코드를 추가하는 것은 **선택사항**입니다
- 로컬 개발 환경에서는 `root` 사용자로 충분합니다
- **AWS RDS에 `proxy_admin` 사용자를 생성하는 것이 필수**입니다
- DMS를 사용하여 데이터를 마이그레이션할 때 사용자 정보는 자동으로 마이그레이션되지 않으므로, 수동으로 생성해야 합니다
