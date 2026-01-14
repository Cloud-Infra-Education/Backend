# 설정 완료 요약

## ✅ 완료된 작업

### 1. 보안 그룹 규칙
- ✅ Lambda 보안 그룹 → DB 클러스터 (3306 포트) 규칙이 이미 존재합니다
- 위치: `Terraform/modules/database/security-group.tf` 81-89번 줄
- 규칙명: `kor_lambda_to_db`

### 2. Lambda 코드 수정
- ✅ `mysql_native_password` 인증 플러그인 사용으로 변경
- ✅ 클러스터 엔드포인트 직접 연결 지원
- 파일: `Backend/lambda/video-processor/app.py`

### 3. Terraform 설정
- ✅ Secrets Manager에 admin 사용자 추가 (코드에 포함)
- ✅ RDS Proxy에 admin 인증 추가 (코드에 포함)
- ✅ Lambda 환경 변수에 `DB_CLUSTER_ENDPOINT` 추가 필요

## 📋 다음 단계

### 1. Terraform 적용
```bash
cd /root/Terraform
terraform apply
```

### 2. Docker 이미지 빌드 및 푸시
```bash
cd /root/Backend/lambda/video-processor
# ECR 리포지토리 확인 필요
aws ecr describe-repositories --repository-names yuh-video-processor --region ap-northeast-2

# 이미지 빌드 및 푸시
REGION="ap-northeast-2"
ACCOUNT_ID="404457776061"
REPO_NAME="yuh-video-processor"
IMAGE_TAG="v16"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
docker build -t ${REPO_NAME}:${IMAGE_TAG} .
docker tag ${REPO_NAME}:${IMAGE_TAG} ${ECR_URI}
docker push ${ECR_URI}
```

### 3. 수동으로 사용자 생성 (선택사항)
Lambda가 자동으로 생성하지만, 수동으로 생성하려면:

```bash
# Docker 컨테이너로 접속
docker exec -it ott_mysql mysql \
  -h yuh-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
  -u admin -p \
  ott_db
```

```sql
-- 기존 사용자 삭제 (있는 경우)
DROP USER IF EXISTS 'proxy_admin'@'%';

-- mysql_native_password로 생성
CREATE USER 'proxy_admin'@'%' 
IDENTIFIED WITH mysql_native_password BY 'test1234';

-- 권한 부여
GRANT ALL PRIVILEGES ON ott_db.* TO 'proxy_admin'@'%';
FLUSH PRIVILEGES;

-- 확인
SELECT User, Host, plugin FROM mysql.user WHERE User = 'proxy_admin';
```

## 🔍 확인 사항

1. **보안 그룹**: Lambda SG → DB Cluster (3306) 규칙이 있는지 확인
2. **Secrets Manager**: `formation-lap/db/admin/credentials`에 admin 사용자 정보가 있는지 확인
3. **RDS Proxy**: 인증(Authentication) 섹션에 admin Secrets Manager가 추가되어 있는지 확인
4. **Lambda 환경 변수**: `DB_CLUSTER_ENDPOINT`가 설정되어 있는지 확인

## 📝 참고

- 보안 그룹 규칙은 이미 Terraform 코드에 포함되어 있습니다
- Lambda 코드는 `mysql_native_password`를 사용하도록 수정되었습니다
- 클러스터 엔드포인트 직접 연결을 지원합니다
