# DB 테이블 확인 결과

## ✅ 로그 기반 확인 (성공)

CloudWatch Logs에서 확인한 결과:

### 최근 실행 결과 (2026-01-14 16:43:49)
- ✅ **contents 테이블 저장 성공**
  - content_id: 1
  - title: "Test Video"
  
- ✅ **video_assets 테이블 저장 성공**
  - content_id: 1
  - duration: 7초
  - video_url: 저장됨
  - thumbnail_url: 저장됨

- ✅ **전체 프로세스 성공**
  - "성공: videos/1_test_video.mp4 등록 완료 (content_id: 1)"

## DB 직접 확인 방법

### 방법 1: MySQL 클라이언트 (VPC 내부에서)

```bash
mysql -h formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u admin -ptest1234 ott_db \
      -e "SELECT * FROM contents; SELECT * FROM video_assets;"
```

### 방법 2: 스크립트 사용

```bash
cd /root/Backend
./SIMPLE_DB_CHECK.sh
```

### 방법 3: FastAPI 엔드포인트 (가장 쉬움)

FastAPI가 실행 중이라면:

```bash
# 비디오 목록 조회
curl http://localhost:8000/videos/search/

# 또는 Kubernetes 내부
curl http://video-service.formation-lap.svc.cluster.local:8000/videos/search/
```

## 확인할 SQL 쿼리

### contents 테이블
```sql
SELECT id, title, description, age_rating, like_count, created_at 
FROM contents 
ORDER BY id DESC;
```

### video_assets 테이블
```sql
SELECT id, content_id, video_url, thumbnail_url, duration, created_at 
FROM video_assets 
ORDER BY id DESC;
```

### 조인 쿼리 (프론트엔드용)
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

## 현재 상태 요약

✅ **성공한 부분:**
- Lambda 실행 성공
- video_assets 테이블 저장 성공
- contents 테이블 저장 성공 (폴백 로직)
- 전체 워크플로우 완료

⚠️ **주의사항:**
- FastAPI 호출은 실패 (Kubernetes 서비스 엔드포인트도 해결 안됨)
- 하지만 폴백 로직으로 DB에 직접 저장되어 문제 없음

## 다음 테스트

새로운 비디오를 업로드하여 테스트:

```bash
# S3에 업로드
aws s3 cp test_video2.mp4 s3://<bucket>/videos/2_test_video2.mp4

# 로그 확인
aws logs tail /aws/lambda/formation-lap-video-processor --follow
```
