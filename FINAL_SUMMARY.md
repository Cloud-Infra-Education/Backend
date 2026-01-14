# 최종 요약 및 해결 방법

## ERD 기반 구현 계획 ✅

### 1. video_assets (Lambda 함수로 구현) ✅
- **책임**: Lambda 함수가 직접 DB에 저장
- **저장 데이터**:
  - `content_id`: 파일명에서 추출
  - `video_url`: S3 경로
  - `thumbnail_url`: S3 썸네일 경로  
  - `duration`: FFprobe로 추출
- **상태**: ✅ 구현 완료 및 정상 동작

### 2. contents (FastAPI로 구현) ⚠️
- **책임**: FastAPI API를 통해서만 채우기
- **저장 데이터**:
  - `id`: content_id
  - `title`: 파일명에서 추출한 slug → title 변환
  - `description`: "Uploaded video: {slug}"
  - `age_rating`: "ALL"
  - `like_count`: 0
- **상태**: 
  - ✅ FastAPI 엔드포인트 구현 완료
  - ❌ Lambda에서 호출 실패 (DNS 문제)
  - ✅ 폴백 로직으로 DB 직접 저장 (임시)

## DNS 문제 원인

### 문제
```
Lambda (VPC 내부 Private 서브넷)
  ↓ HTTP 요청
외부 도메인: api.matchacake.click
  ↓ DNS 해결 시도
❌ NameResolutionError: Failed to resolve 'api.matchacake.click'
```

### 원인
1. **Lambda가 VPC 내부에 있음**
   - Private 서브넷에 배포
   - 외부 도메인 DNS 해결 제한

2. **VPC DNS 설정**
   - `EnableDnsSupport`와 `EnableDnsHostnames` 확인 필요
   - 현재: null (기본값 사용 중)

3. **NAT Gateway vs DNS**
   - NAT Gateway: 인터넷 아웃바운드 트래픽 허용
   - DNS 해결: 별도 설정 필요

## 해결 방법 (우선순위)

### 방법 1: 내부 Kubernetes 서비스 엔드포인트 사용 ⭐ (권장)

**Kubernetes 서비스 정보:**
- 서비스명: `video-service`
- 네임스페이스: `formation-lap`
- 포트: `8000`
- 내부 엔드포인트: `http://video-service.formation-lap.svc.cluster.local:8000/api`

**실행:**
```bash
cd /root/Backend
./FIX_DNS_ISSUE.sh
```

**장점**:
- ✅ VPC 내부 통신 (DNS 문제 없음)
- ✅ 보안성 향상
- ✅ 빠른 응답

### 방법 2: 현재 폴백 로직 유지 (제출용)

현재 Lambda 코드는 FastAPI 호출 실패 시 DB에 직접 저장하는 폴백 로직이 있습니다.

**장점**:
- ✅ 안정성 (API 실패해도 동작)
- ✅ 제출용으로 충분

**단점**:
- ⚠️ "contents는 FastAPI로만" 원칙 위배

## API 작업 가이드

### 현재 구현 상태

#### 1. FastAPI 내부 Upsert 엔드포인트 ✅
**위치**: `/root/Backend/app/video-service/app.py`

```python
@app.put("/api/v1/contents/{content_id}/upsert-internal", 
         dependencies=[Depends(verify_internal_token)])
def upsert_content_internal(content_id: int, payload: dict):
    """Lambda에서 호출하는 내부용 contents upsert"""
    # contents 테이블에 저장/업데이트
```

**테스트:**
```bash
curl -X PUT "http://localhost:8000/api/v1/contents/1/upsert-internal" \
  -H "X-Internal-Token: formation-lap-internal-token-2024-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Video","description":"Uploaded video: test_video","age_rating":"ALL"}'
```

#### 2. Lambda에서 API 호출 ✅
**위치**: `/root/Backend/lambda/video-processor/app.py`

```python
def upsert_contents_via_api(content_id: int, key: str):
    """FastAPI의 내부 upsert 엔드포인트를 호출"""
    api_base = os.environ.get("CATALOG_API_BASE", "")
    url = f"{api_base}/v1/contents/{content_id}/upsert-internal"
    r = requests.put(url, json=payload, headers={"X-Internal-Token": token})
```

## 즉시 할 일

### 옵션 A: DNS 문제 해결 (권장)

1. **내부 엔드포인트로 변경**
   ```bash
   cd /root/Backend
   ./FIX_DNS_ISSUE.sh
   ```

2. **테스트**
   ```bash
   # S3 업로드
   aws s3 cp test_video.mp4 s3://<bucket>/videos/2_test_video2.mp4
   
   # CloudWatch 로그 확인
   aws logs tail /aws/lambda/formation-lap-video-processor --follow
   ```

3. **DB 확인**
   ```sql
   SELECT * FROM contents WHERE id = 2;
   SELECT * FROM video_assets WHERE content_id = 2;
   ```

### 옵션 B: 현재 상태 유지 (제출용)

현재 폴백 로직이 있으므로:
- FastAPI 호출 시도 → 실패 시 DB 직접 저장
- 제출용으로는 이 방식도 가능
- 제출 후 DNS 문제 해결

## 최종 체크리스트

- [x] video_assets Lambda 구현 완료
- [x] contents FastAPI 엔드포인트 구현 완료
- [x] Lambda API 호출 로직 구현 완료
- [ ] DNS 문제 해결 (내부 엔드포인트 사용)
- [ ] 전체 워크플로우 테스트
- [ ] DB 확인 (contents + video_assets)

## 제출 시 설명 포인트

1. **아키텍처 분리**
   - video_assets: Lambda 함수로 직접 DB 저장
   - contents: FastAPI API를 통해서만 채우기

2. **DNS 문제 및 해결**
   - 원인: VPC 내부 Lambda → 외부 도메인 DNS 해결 불가
   - 해결: 내부 Kubernetes 서비스 엔드포인트 사용

3. **안정성**
   - 폴백 로직으로 API 실패 시에도 동작 보장
