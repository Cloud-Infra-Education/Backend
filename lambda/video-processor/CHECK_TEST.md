# Video Processor 테스트 확인 가이드

## 1. Lambda 함수가 트리거되었는지 확인

### CloudWatch Logs 확인

```bash
# 로그 그룹 확인
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda" | grep video-processor

# 최근 로그 확인 (실시간)
aws logs tail /aws/lambda/{your-team}-video-processor --follow

# 최근 로그 확인 (마지막 50줄)
aws logs tail /aws/lambda/{your-team}-video-processor --since 10m
```

### AWS 콘솔에서 확인
1. CloudWatch → Log groups
2. `/aws/lambda/{your-team}-video-processor` 선택
3. 최근 로그 스트림 확인

### 확인할 로그 메시지
다음 메시지들이 순서대로 나타나야 합니다:
```
환경 변수 확인 - DB_HOST: ..., DB_USER: ..., DB_NAME: ...
영상 처리 시작: videos/...
DB 연결 시도: ...
DB 연결 성공
파일명에서 content_id 추출: ... (또는 메타데이터에서 추출)
추출된 메타데이터: ...
contents 테이블에 등록 완료 (content_id: ...)
video_assets 테이블에 등록 완료 (content_id: ...)
성공: videos/... 등록 완료
```

## 2. DB에 데이터가 저장되었는지 확인

### RDS Proxy를 통해 DB 접속

```bash
# RDS Proxy 엔드포인트 확인 (Terraform output 또는 콘솔에서)
mysql -h {rds-proxy-endpoint} -u {db-user} -p{db-password} ott_db
```

### SQL 쿼리로 확인

```sql
-- contents 테이블 확인 (최근 등록된 것부터)
SELECT * FROM contents ORDER BY id DESC LIMIT 5;

-- video_assets 테이블 확인
SELECT * FROM video_assets ORDER BY id DESC LIMIT 5;

-- 두 테이블 조인해서 확인
SELECT 
    c.id as content_id,
    c.title,
    c.description,
    c.age_rating,
    va.video_url,
    va.thumbnail_url,
    va.duration
FROM contents c
LEFT JOIN video_assets va ON c.id = va.content_id
ORDER BY c.id DESC
LIMIT 5;
```

## 3. S3에 썸네일이 생성되었는지 확인

### AWS CLI로 확인

```bash
# 썸네일 목록 확인
aws s3 ls s3://{your-bucket}/thumbnails/ --recursive

# 특정 썸네일 다운로드해서 확인
aws s3 cp s3://{your-bucket}/thumbnails/thumb_{filename}.jpg ./test-thumbnail.jpg
```

### AWS 콘솔에서 확인
1. S3 버킷 → `thumbnails/` 폴더
2. `thumb_{원본파일명}.jpg` 파일이 생성되었는지 확인

## 4. 문제 진단

### Lambda가 트리거되지 않은 경우

**확인 사항:**
1. 파일 경로가 `videos/`로 시작하는가?
2. 파일 확장자가 `.mp4`인가?
3. S3 버킷 알림이 설정되었는가?

```bash
# S3 버킷 알림 설정 확인
aws s3api get-bucket-notification-configuration --bucket {your-bucket}
```

### Lambda는 실행되었지만 에러가 발생한 경우

**CloudWatch Logs에서 에러 확인:**
```bash
aws logs tail /aws/lambda/{your-team}-video-processor --follow | grep -i error
```

**일반적인 에러:**
- "DB 연결 실패" → 환경 변수 또는 VPC/Security Group 확인
- "메타데이터 추출 실패" → FFprobe 문제, 영상 파일 형식 확인
- "썸네일 추출 실패" → FFmpeg 문제, 영상 파일 확인

### DB에 데이터가 없는 경우

**확인 사항:**
1. Lambda 로그에 "성공: ... 등록 완료" 메시지가 있는가?
2. DB 연결이 성공했는가?
3. 트랜잭션이 커밋되었는가?

```sql
-- 최근 실행된 쿼리 확인 (MySQL 5.7+)
SHOW PROCESSLIST;

-- 테이블 구조 확인
DESCRIBE contents;
DESCRIBE video_assets;
```

## 5. 성공 확인 체크리스트

- [ ] CloudWatch Logs에 "성공: ... 등록 완료" 메시지 있음
- [ ] `contents` 테이블에 새 레코드 추가됨
- [ ] `video_assets` 테이블에 새 레코드 추가됨
- [ ] S3에 썸네일 파일 생성됨 (`thumbnails/` 경로)
- [ ] `video_url`과 `thumbnail_url`이 올바른 S3 URI로 저장됨
- [ ] `duration` 값이 올바르게 저장됨

## 6. 빠른 확인 명령어

```bash
# 1. Lambda 로그 확인 (최근 10분)
aws logs tail /aws/lambda/{your-team}-video-processor --since 10m

# 2. S3 썸네일 확인
aws s3 ls s3://{your-bucket}/thumbnails/ --recursive | tail -5

# 3. DB 확인 (RDS Proxy 엔드포인트 필요)
mysql -h {rds-proxy-endpoint} -u {db-user} -p{db-password} ott_db -e "SELECT * FROM contents ORDER BY id DESC LIMIT 3;"
mysql -h {rds-proxy-endpoint} -u {db-user} -p{db-password} ott_db -e "SELECT * FROM video_assets ORDER BY id DESC LIMIT 3;"
```
