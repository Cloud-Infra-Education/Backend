# Lambda ↔ FastAPI 통합 가이드

## 완료된 작업

### 1. FastAPI 내부 Upsert 엔드포인트
- ✅ `/root/Backend/app/api/v1/routes/contents_internal.py` 생성
- ✅ `PUT /api/v1/contents/{content_id}/upsert-internal` 엔드포인트 추가
- ✅ `X-Internal-Token` 헤더로 인증
- ✅ `config.py`에 `INTERNAL_TOKEN` 설정 추가
- ✅ `main.py`에 라우터 등록

### 2. Lambda API 호출 로직
- ✅ `upsert_contents_via_api()` 함수 추가
- ✅ 파일명에서 slug 추출 → title 변환
- ✅ `requirements.txt`에 `requests` 추가
- ✅ handler에서 DB insert 전에 API 호출

### 3. Terraform 설정
- ✅ ALB Controller Kubernetes 리소스 주석 처리 (네트워크 문제 해결 전까지)
- ✅ IRSA 모듈은 정상 생성됨

## 다음 단계

### 1. 환경 변수 설정

**FastAPI (.env 또는 Kubernetes Secret):**
```bash
INTERNAL_TOKEN=your_shared_secret_token_here
```

**Lambda 환경 변수:**
```bash
CATALOG_API_BASE=https://api.matchacake.click/api  # 실제 도메인으로 변경
INTERNAL_TOKEN=your_shared_secret_token_here  # FastAPI와 동일한 값
```

### 2. FastAPI 배포 및 테스트

```bash
# FastAPI 배포 후 테스트
export API_BASE="https://api.matchacake.click/api"
export INTERNAL_TOKEN="your_shared_secret_token_here"

curl -X PUT "$API_BASE/v1/contents/1/upsert-internal" \
  -H "X-Internal-Token: $INTERNAL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Video","description":"Uploaded video: test_video","age_rating":"ALL"}'
```

### 3. Lambda 재배포

- `requirements.txt`에 `requests`가 추가되었으므로 컨테이너 이미지 재빌드 필요
- 환경 변수 `CATALOG_API_BASE`, `INTERNAL_TOKEN` 설정

### 4. 전체 플로우 테스트

1. S3에 영상 업로드 (예: `videos/1_test_video.mp4`)
2. Lambda 실행 확인 (CloudWatch 로그)
3. DB 확인:
   ```sql
   SELECT * FROM contents WHERE id=1;
   SELECT * FROM video_assets WHERE content_id=1;
   ```

## 파일명 형식

- 형식: `{content_id}_{slug}.mp4`
- 예: `1_test_video.mp4` → `content_id=1`, `title="Test Video"`

## 처리 순서

1. 파일명에서 `content_id` 추출
2. FastAPI upsert API 호출 → `contents` 테이블에 title/description/age_rating 저장
3. `video_assets` 테이블에 video_url/thumbnail_url/duration 저장

## 문제 해결

### Lambda가 API를 호출하지 못하는 경우

1. **네트워크 문제**: Lambda가 VPC 내부에 있으면 외부 도메인 호출이 막힐 수 있음
   - 해결: NAT Gateway 경로 확인 또는 Lambda를 VPC 밖으로 이동

2. **환경 변수 미설정**: `CATALOG_API_BASE` 또는 `INTERNAL_TOKEN`이 없으면 API 호출 건너뜀
   - 해결: Lambda 환경 변수 확인

3. **API 엔드포인트 오류**: 401/403/404 오류
   - 해결: 도메인, 경로, 토큰 확인
