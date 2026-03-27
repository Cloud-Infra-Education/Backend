# 아키텍처 설명 및 DNS 문제 해결

## ERD 기반 구현 계획

### ✅ video_assets (Lambda 함수로 구현)
- **책임**: Lambda 함수가 직접 DB에 저장
- **저장 데이터**:
  - `content_id`: 파일명에서 추출 또는 메타데이터에서 가져옴
  - `video_url`: S3 경로 (s3:// 형식)
  - `thumbnail_url`: S3 썸네일 경로
  - `duration`: FFprobe로 추출한 영상 길이
- **현재 상태**: ✅ 구현 완료

### ✅ contents (FastAPI로 구현)
- **책임**: FastAPI API를 통해서만 채우기
- **저장 데이터**:
  - `id`: content_id
  - `title`: 파일명에서 추출한 slug를 title로 변환
  - `description`: "Uploaded video: {slug}"
  - `age_rating`: "ALL" (기본값)
  - `like_count`: 0 (기본값)
- **현재 상태**: ⚠️ FastAPI 엔드포인트는 구현됨, 하지만 Lambda에서 호출 실패 (DNS 문제)

## DNS 문제 원인 분석

### 문제 상황
```
Lambda (VPC 내부 Private 서브넷)
  ↓
외부 도메인 해결 시도: api.matchacake.click
  ↓
NameResolutionError: Failed to resolve 'api.matchacake.click'
```

### 원인
1. **Lambda가 VPC 내부에 있음**
   - Lambda는 Private 서브넷에 배포됨
   - VPC 내부에서는 외부 도메인 DNS 해결이 제한될 수 있음

2. **DNS 해결 경로 문제**
   - VPC의 DNS 설정이 외부 도메인 해결을 지원하지 않음
   - 또는 Route53 Resolver 설정이 필요할 수 있음

3. **NAT Gateway는 있지만 DNS는 별개**
   - NAT Gateway: 인터넷 아웃바운드 트래픽 허용
   - DNS 해결: VPC DNS 설정 또는 Route53 Resolver 필요

### 확인 사항
```bash
# VPC DNS 설정 확인
aws ec2 describe-vpcs --vpc-ids vpc-0df467378a7d3aa20 \
  --query 'Vpcs[0].{EnableDnsHostnames:EnableDnsHostnames,EnableDnsSupport:EnableDnsSupport}'

# Route53 Resolver 확인
aws route53resolver list-resolver-endpoints --region ap-northeast-2
```

## 해결 방법

### 방법 1: 내부 Kubernetes 서비스 엔드포인트 사용 (권장)

**FastAPI가 Kubernetes에 배포되어 있다면:**

```bash
# Kubernetes 서비스 확인
kubectl get svc -A | grep -i "catalog\|api\|fastapi"

# Lambda 환경 변수 변경
CATALOG_API_BASE = "http://catalog-service.default.svc.cluster.local/api"
# 또는
CATALOG_API_BASE = "http://<service-name>.<namespace>.svc.cluster.local/api"
```

**장점**:
- VPC 내부 통신으로 DNS 문제 없음
- 보안성 향상 (내부 네트워크만 사용)
- 비용 절감 (외부 트래픽 없음)

### 방법 2: VPC DNS 설정 확인 및 수정

```bash
# VPC DNS 지원 활성화
aws ec2 modify-vpc-attribute \
  --vpc-id vpc-0df467378a7d3aa20 \
  --enable-dns-support \
  --enable-dns-hostnames
```

### 방법 3: Route53 Private Hosted Zone 사용

```bash
# Private Hosted Zone 생성
aws route53 create-hosted-zone \
  --name api.matchacake.click \
  --vpc VPCRegion=ap-northeast-2,VPCId=vpc-0df467378a7d3aa20 \
  --caller-reference $(date +%s)
```

### 방법 4: 내부 ALB/NLB 엔드포인트 사용

FastAPI가 ALB/NLB 뒤에 있다면:
- 내부 ALB DNS 이름 사용
- 예: `internal-api-1234567890.ap-northeast-2.elb.amazonaws.com`

## API 작업 가이드

### 현재 구현 상태

#### 1. FastAPI 내부 Upsert 엔드포인트 ✅
**위치**: `/root/Backend/app/video-service/app.py`

```python
@app.put("/api/v1/contents/{content_id}/upsert-internal", 
         dependencies=[Depends(verify_internal_token)])
def upsert_content_internal(content_id: int, payload: dict):
    """
    Lambda에서 호출하는 내부용 contents upsert 엔드포인트
    payload: {"title": "...", "description": "...", "age_rating": "..."}
    """
    # contents 테이블에 저장/업데이트
```

#### 2. Lambda에서 API 호출 ✅
**위치**: `/root/Backend/lambda/video-processor/app.py`

```python
def upsert_contents_via_api(content_id: int, key: str):
    """FastAPI의 내부 upsert 엔드포인트를 호출"""
    api_base = os.environ.get("CATALOG_API_BASE", "").rstrip("/")
    token = os.environ.get("INTERNAL_TOKEN", "")
    
    url = f"{api_base}/v1/contents/{content_id}/upsert-internal"
    r = requests.put(url, json=payload, headers={"X-Internal-Token": token})
```

### API 작업 체크리스트

#### Step 1: FastAPI 엔드포인트 확인
```bash
# FastAPI 실행
cd /root/Backend/app/video-service
uvicorn app:app --host 0.0.0.0 --port 8000

# 테스트
curl -X PUT "http://localhost:8000/api/v1/contents/1/upsert-internal" \
  -H "X-Internal-Token: formation-lap-internal-token-2024-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Video","description":"Uploaded video: test_video","age_rating":"ALL"}'
```

#### Step 2: Lambda 환경 변수 설정
```bash
# 현재 설정 확인
aws lambda get-function-configuration \
  --function-name formation-lap-video-processor \
  --query 'Environment.Variables' \
  --region ap-northeast-2

# 내부 엔드포인트로 변경 (방법 1 사용 시)
aws lambda update-function-configuration \
  --function-name formation-lap-video-processor \
  --environment "Variables={
    CATALOG_API_BASE=http://catalog-service.default.svc.cluster.local/api,
    INTERNAL_TOKEN=formation-lap-internal-token-2024-secret-key,
    ...
  }" \
  --region ap-northeast-2
```

#### Step 3: 전체 워크플로우 테스트
1. S3에 비디오 업로드
2. Lambda 실행 (video_assets 저장)
3. Lambda가 FastAPI 호출 (contents 저장)
4. DB 확인

## 권장 해결 순서

### 즉시 할 일 (제출 전)
1. **내부 엔드포인트 확인**
   ```bash
   kubectl get svc -A
   ```

2. **Lambda 환경 변수 업데이트** (내부 엔드포인트 사용)
   ```bash
   # 내부 서비스 엔드포인트로 변경
   CATALOG_API_BASE=http://<service-name>.<namespace>.svc.cluster.local/api
   ```

3. **테스트**
   - S3 업로드
   - CloudWatch 로그 확인
   - DB 확인 (contents + video_assets)

### 장기 개선 (제출 후)
- VPC DNS 설정 최적화
- Route53 Private Hosted Zone 설정
- 모니터링 및 알림 추가

## 현재 Lambda 코드 상태

**주의**: 현재 Lambda 코드는 FastAPI 호출 실패 시 DB에 직접 저장하는 폴백 로직이 있습니다.

**원래 의도대로 하려면** (contents는 FastAPI로만):
- 폴백 로직 제거
- FastAPI 호출만 사용
- DNS 문제 해결 필수

**현재 폴백 로직 유지하려면**:
- FastAPI 호출 시도 → 실패 시 DB 직접 저장
- 제출용으로는 이 방식도 가능 (안정성 향상)
