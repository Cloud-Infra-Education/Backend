# DNS 문제 해결 가이드

## 문제 상황

```
Lambda (VPC 내부 Private 서브넷)
  ↓ HTTP 요청
외부 도메인: api.matchacake.click
  ↓ DNS 해결 시도
❌ NameResolutionError: Failed to resolve 'api.matchacake.click'
```

## 원인 분석

### 1. Lambda가 VPC 내부에 있음
- Lambda는 Private 서브넷에 배포됨
- VPC 내부에서는 외부 도메인 DNS 해결이 제한될 수 있음

### 2. VPC DNS 설정
- VPC의 `EnableDnsSupport`와 `EnableDnsHostnames` 설정 확인 필요
- 기본적으로 활성화되어 있지만, 확인 필요

### 3. NAT Gateway vs DNS
- **NAT Gateway**: 인터넷 아웃바운드 트래픽 허용 (HTTP/HTTPS)
- **DNS 해결**: 별도의 DNS 설정 필요 (VPC DNS 또는 Route53)

## 해결 방법

### 방법 1: 내부 Kubernetes 서비스 엔드포인트 사용 (가장 권장) ⭐

**FastAPI가 Kubernetes에 배포되어 있다면:**

#### 1-1. Kubernetes 서비스 확인
```bash
kubectl get svc -A | grep -i "video\|catalog\|api"
```

#### 1-2. 서비스 엔드포인트 형식
```
http://<service-name>.<namespace>.svc.cluster.local
```

예시:
- 서비스명: `video-service`
- 네임스페이스: `default`
- 엔드포인트: `http://video-service.default.svc.cluster.local`

#### 1-3. Lambda 환경 변수 업데이트
```bash
aws lambda update-function-configuration \
  --function-name formation-lap-video-processor \
  --environment "Variables={
    CATALOG_API_BASE=http://video-service.default.svc.cluster.local/api,
    INTERNAL_TOKEN=formation-lap-internal-token-2024-secret-key,
    DB_HOST=formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com,
    DB_USER=admin,
    DB_PASSWORD=test1234,
    DB_NAME=ott_db
  }" \
  --region ap-northeast-2
```

**장점**:
- ✅ VPC 내부 통신 (DNS 문제 없음)
- ✅ 보안성 향상 (외부 노출 없음)
- ✅ 비용 절감 (NAT Gateway 트래픽 감소)
- ✅ 빠른 응답 (내부 네트워크)

### 방법 2: VPC DNS 설정 확인 및 수정

```bash
# 현재 설정 확인
aws ec2 describe-vpcs --vpc-ids vpc-0df467378a7d3aa20 \
  --query 'Vpcs[0].{EnableDnsHostnames:EnableDnsHostnames,EnableDnsSupport:EnableDnsSupport}'

# DNS 지원 활성화 (필요 시)
aws ec2 modify-vpc-attribute \
  --vpc-id vpc-0df467378a7d3aa20 \
  --enable-dns-support

aws ec2 modify-vpc-attribute \
  --vpc-id vpc-0df467378a7d3aa20 \
  --enable-dns-hostnames
```

### 방법 3: Route53 Private Hosted Zone 사용

```bash
# Private Hosted Zone 생성
aws route53 create-hosted-zone \
  --name api.matchacake.click \
  --vpc VPCRegion=ap-northeast-2,VPCId=vpc-0df467378a7d3aa20 \
  --caller-reference $(date +%s)

# A 레코드 추가 (ALB 또는 NLB 엔드포인트)
aws route53 change-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.matchacake.click",
        "Type": "A",
        "AliasTarget": {
          "DNSName": "<alb-dns-name>",
          "EvaluateTargetHealth": false,
          "HostedZoneId": "<alb-zone-id>"
        }
      }
    }]
  }'
```

### 방법 4: 내부 ALB/NLB 엔드포인트 사용

FastAPI가 ALB/NLB 뒤에 있다면:
- 내부 ALB DNS 이름 사용
- 예: `internal-api-1234567890.ap-northeast-2.elb.amazonaws.com`

## 현재 Lambda 코드 상태

### 현재 구현 (폴백 로직 포함)
```python
try:
    upsert_contents_via_api(content_id, key)  # FastAPI 호출 시도
except Exception as api_error:
    # FastAPI 실패 시 DB에 직접 저장 (폴백)
    # contents 테이블에 직접 저장
```

### 원래 의도대로 하려면 (contents는 FastAPI로만)
폴백 로직을 제거하고 FastAPI 호출만 사용:
- DNS 문제 해결 필수
- FastAPI 호출 실패 시 에러 발생 (의도적)

## 권장 해결 순서

### 즉시 할 일 (제출 전)

1. **Kubernetes 서비스 확인**
   ```bash
   kubectl get svc -A
   ```

2. **Lambda 환경 변수 업데이트** (내부 엔드포인트 사용)
   ```bash
   # 서비스 이름 확인 후
   CATALOG_API_BASE=http://video-service.default.svc.cluster.local/api
   ```

3. **테스트**
   - S3 업로드
   - CloudWatch 로그 확인
   - DB 확인 (contents + video_assets)

### 대안 (제출용 빠른 해결)

현재 폴백 로직이 있으므로:
- FastAPI 호출 시도 → 실패 시 DB 직접 저장
- 제출용으로는 이 방식도 가능 (안정성 향상)
- 제출 후 DNS 문제 해결

## API 작업 요약

### ERD 기반 구현

#### ✅ video_assets (Lambda 함수)
- Lambda가 직접 DB에 저장
- `content_id`, `video_url`, `thumbnail_url`, `duration`

#### ✅ contents (FastAPI)
- FastAPI API를 통해서만 채우기
- `id`, `title`, `description`, `age_rating`, `like_count`

### 현재 상태
- ✅ FastAPI 내부 upsert 엔드포인트 구현됨
- ✅ Lambda에서 API 호출 로직 구현됨
- ❌ DNS 문제로 API 호출 실패
- ✅ 폴백 로직으로 DB 직접 저장 (임시 해결)

### 최종 목표
- FastAPI 호출 성공 → contents 테이블 자동 채움
- DNS 문제 해결 필수
