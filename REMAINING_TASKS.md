# 남은 작업 체크리스트

## 현재 상태 ✅❌

### ✅ 성공한 부분
1. **Lambda 핵심 기능 정상 동작**
   - FFmpeg/FFprobe 정상 작동
   - RDS Proxy 연결 성공
   - `video_assets` 테이블 저장 성공 ✅
   - 비디오 처리 완료

2. **FastAPI 내부 upsert 엔드포인트**
   - `/api/v1/contents/{id}/upsert-internal` 구현 완료
   - INTERNAL_TOKEN 인증 구현 완료

### ❌ 문제점
1. **FastAPI 호출 실패 (DNS 해결 불가)**
   - Lambda가 VPC 내부에 있어 외부 도메인(`api.matchacake.click`) 해결 불가
   - 결과: `contents` 테이블이 자동으로 채워지지 않음

## 남은 작업

### 옵션 1: FastAPI 호출 문제 해결 (권장 - 제출용 완벽)

#### 방법 A: 내부 Kubernetes 서비스 엔드포인트 사용
```python
# Lambda 환경 변수 변경
CATALOG_API_BASE = "http://catalog-service.default.svc.cluster.local/api"
# 또는
CATALOG_API_BASE = "http://<internal-alb-dns>/api"
```

**장점**: VPC 내부 통신으로 DNS 문제 해결
**단점**: Kubernetes 서비스 엔드포인트 확인 필요

#### 방법 B: Lambda에서 직접 DB에 contents 저장 (임시)
FastAPI 호출 실패 시, Lambda에서 직접 `contents` 테이블에 저장

**장점**: 빠른 해결
**단점**: "API로만 contents 채우기" 원칙 위배

### 옵션 2: 현재 상태로 제출 + 수동 처리 (빠른 제출)

**핵심 기능은 정상 동작**하므로:
1. `video_assets` 테이블은 자동으로 채워짐 ✅
2. `contents` 테이블은 수동으로 채우거나, 나중에 FastAPI 호출

**제출 시 설명**:
- "Lambda는 video_assets를 자동 저장"
- "contents는 FastAPI API를 통해 채움 (현재 네트워크 설정으로 인해 자동화는 보류)"

## 추천 작업 순서

### 즉시 할 일 (제출 전 필수)

#### 1. DB 상태 확인
```sql
-- video_assets 확인 (자동 저장됨)
SELECT * FROM video_assets WHERE content_id = 1;

-- contents 확인 (수동으로 채워야 할 수도 있음)
SELECT * FROM contents WHERE id = 1;
```

#### 2. contents 테이블 수동 채우기 (필요 시)
```sql
-- Lambda가 실패한 경우 수동으로 채우기
INSERT INTO contents (id, title, description, age_rating, like_count)
VALUES (1, 'Test Video', 'Uploaded video: test_video', 'ALL', 0)
ON DUPLICATE KEY UPDATE
  title = 'Test Video',
  description = 'Uploaded video: test_video',
  age_rating = 'ALL';
```

#### 3. FastAPI 호출 문제 해결 (선택)

**방법 1: Lambda 환경 변수 변경 (내부 엔드포인트)**
```bash
# Kubernetes 서비스 엔드포인트 확인
kubectl get svc -A | grep catalog

# Lambda 환경 변수 업데이트
aws lambda update-function-configuration \
  --function-name formation-lap-video-processor \
  --environment "Variables={
    CATALOG_API_BASE=http://catalog-service.default.svc.cluster.local/api,
    INTERNAL_TOKEN=formation-lap-internal-token-2024-secret-key,
    ...
  }"
```

**방법 2: Lambda 코드 수정 (DB 직접 저장)**
FastAPI 호출 실패 시, Lambda에서 직접 contents 저장

### 제출용 증빙 자료 준비

1. **CloudWatch 로그**
   - ✅ video_assets 저장 성공 로그
   - ⚠️ FastAPI 호출 실패 로그 (설명 필요)

2. **DB 쿼리 결과**
   ```sql
   -- video_assets (자동 저장)
   SELECT * FROM video_assets;
   
   -- contents (수동 또는 API로 채움)
   SELECT * FROM contents;
   ```

3. **전체 워크플로우 설명**
   - S3 업로드 → Lambda 실행 → video_assets 저장 ✅
   - FastAPI 호출 → contents 저장 (현재 네트워크 이슈로 수동 처리)

## 빠른 해결 방법 (지금 바로)

### 방법 1: contents 수동 채우기 (가장 빠름)
```sql
-- 파일명 기반으로 contents 채우기
INSERT INTO contents (id, title, description, age_rating, like_count)
SELECT 
  va.content_id,
  CONCAT(UCASE(LEFT(SUBSTRING_INDEX(SUBSTRING_INDEX(va.video_url, '/', -1), '_', -1), 1), 1),
         SUBSTRING(SUBSTRING_INDEX(SUBSTRING_INDEX(va.video_url, '/', -1), '_', -1), 2)) as title,
  CONCAT('Uploaded video: ', SUBSTRING_INDEX(SUBSTRING_INDEX(va.video_url, '/', -1), '_', -1)) as description,
  'ALL' as age_rating,
  0 as like_count
FROM video_assets va
LEFT JOIN contents c ON va.content_id = c.id
WHERE c.id IS NULL;
```

### 방법 2: Lambda 코드 수정 (DB 직접 저장)
FastAPI 호출 실패 시, Lambda에서 직접 contents 저장하도록 수정

## 최종 체크리스트

- [ ] DB에서 video_assets 확인 (자동 저장됨)
- [ ] DB에서 contents 확인 (수동 또는 API로 채움)
- [ ] FastAPI 호출 문제 해결 (선택)
- [ ] 제출용 증빙 자료 준비
- [ ] 전체 워크플로우 문서화

## 제출 시 설명 포인트

1. **핵심 기능 완성**: video_assets 자동 저장 ✅
2. **API 연동**: FastAPI 내부 upsert 엔드포인트 구현 완료 ✅
3. **네트워크 이슈**: VPC 내부 Lambda → 외부 도메인 DNS 해결 문제
4. **해결 방안**: 내부 엔드포인트 사용 또는 수동 처리
