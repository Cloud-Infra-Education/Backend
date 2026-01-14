# DB 테이블 확인 방법

## 방법 1: CloudWatch Logs에서 확인 (가장 쉬움) ⭐

Lambda가 성공적으로 실행되었는지 로그로 확인:

```bash
# 최근 로그 확인
aws logs tail /aws/lambda/formation-lap-video-processor --since 30m --follow --region ap-northeast-2

# 성공 메시지 확인
aws logs tail /aws/lambda/formation-lap-video-processor --since 1h --region ap-northeast-2 | grep -E "성공|완료|contents|video_assets"
```

**성공 로그 예시:**
```
[INFO] FastAPI upsert 성공: content_id=3, title=Test Video
[INFO] contents 테이블에 직접 저장 완료 (content_id: 3, title: Test Video)
[INFO] video_assets 테이블에 등록 완료 (content_id: 3)
[INFO] 성공: videos/3_test_video3.mp4 등록 완료 (content_id: 3)
```

## 방법 2: FastAPI 엔드포인트로 확인

FastAPI가 실행 중이라면:

```bash
# 비디오 목록 조회 (contents + video_assets 조인)
curl http://video-service.formation-lap.svc.cluster.local:8000/videos/search/

# 또는 로컬에서
curl http://localhost:8000/videos/search/
```

## 방법 3: MySQL 클라이언트 (VPC 내부 또는 Bastion)

### VPC 내부 EC2에서 실행:

```bash
mysql -h formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u admin -ptest1234 ott_db \
      -e "SELECT * FROM contents; SELECT * FROM video_assets;"
```

### 스크립트 사용:

```bash
cd /root/Backend
./CHECK_DB_TABLES.sh
```

## 방법 4: Python 스크립트 (VPC 내부에서)

```bash
cd /root/Backend
python3 CHECK_DB_PYTHON.py
```

## 방법 5: CloudWatch Logs Insights (고급)

```bash
aws logs start-query \
  --log-group-name /aws/lambda/formation-lap-video-processor \
  --start-time $(($(date +%s) - 3600)) \
  --end-time $(date +%s) \
  --query-string "fields @timestamp, @message | filter @message like /성공|완료|contents|video_assets/ | sort @timestamp desc" \
  --region ap-northeast-2
```

## 확인할 내용

### 1. contents 테이블
```sql
SELECT id, title, description, age_rating, like_count, created_at 
FROM contents 
ORDER BY id DESC;
```

### 2. video_assets 테이블
```sql
SELECT id, content_id, video_url, thumbnail_url, duration, created_at 
FROM video_assets 
ORDER BY id DESC;
```

### 3. 조인 쿼리 (프론트엔드용)
```sql
SELECT 
    c.id,
    c.title,
    c.description,
    c.age_rating,
    c.like_count,
    va.video_url,
    va.thumbnail_url,
    va.duration
FROM contents c
LEFT JOIN video_assets va ON c.id = va.content_id
ORDER BY c.id DESC;
```

## 빠른 확인 (로그 기반)

로그에 다음 메시지가 있으면 성공:
- ✅ "FastAPI upsert 성공" 또는 "contents 테이블에 직접 저장 완료"
- ✅ "video_assets 테이블에 등록 완료"
- ✅ "성공: videos/... 등록 완료"
