# 로컬 작업 빠른 시작 가이드

## ✅ 완료된 작업

1. ✅ FastAPI 내부 upsert 엔드포인트 추가 (`/api/v1/contents/{id}/upsert-internal`)
2. ✅ INTERNAL_TOKEN 설정 추가
3. ✅ Lambda 코드는 이미 구현되어 있음

## 로컬에서 테스트하기

### Step 1: FastAPI 실행

```bash
cd /root/Backend/app/video-service

# 환경 변수 설정
export DB_HOST="localhost"  # 또는 실제 RDS Proxy
export DB_USER="admin"
export DB_PASSWORD="test1234"
export DB_NAME="ott_db"
export INTERNAL_TOKEN="formation-lap-internal-token-2024-secret-key"

# FastAPI 실행
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Step 2: 내부 Upsert API 테스트

**다른 터미널에서:**

```bash
cd /root/Backend

export API_BASE="http://localhost:8000"
export INTERNAL_TOKEN="formation-lap-internal-token-2024-secret-key"

# 테스트 실행
./scripts/test_internal_api.sh 1
```

**또는 직접 curl:**

```bash
curl -X PUT "http://localhost:8000/api/v1/contents/1/upsert-internal" \
  -H "X-Internal-Token: formation-lap-internal-token-2024-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Video",
    "description": "Uploaded video: test_video",
    "age_rating": "ALL"
  }'
```

**예상 응답:**
```json
{
  "id": 1,
  "title": "Test Video",
  "age_rating": "ALL"
}
```

### Step 3: Lambda 로직 로컬 테스트

```python
# test_lambda_local.py
import os
import sys

# 환경 변수 설정
os.environ["CATALOG_API_BASE"] = "http://localhost:8000"
os.environ["INTERNAL_TOKEN"] = "formation-lap-internal-token-2024-secret-key"

# Lambda 코드 경로 추가
sys.path.insert(0, "/root/Backend/lambda/video-processor")

from app import extract_slug_from_filename, slug_to_title, upsert_contents_via_api

# 테스트
key = "videos/1_test_video.mp4"
slug = extract_slug_from_filename(key)  # "test_video"
title = slug_to_title(slug)  # "Test Video"

print(f"Slug: {slug}")
print(f"Title: {title}")

# FastAPI 호출 테스트 (FastAPI가 실행 중이어야 함)
try:
    upsert_contents_via_api(1, key)
    print("✅ FastAPI 호출 성공!")
except Exception as e:
    print(f"❌ FastAPI 호출 실패: {e}")
```

### Step 4: DB 확인

```sql
-- contents 테이블 확인
SELECT * FROM contents WHERE id = 1;

-- video_assets 테이블 확인
SELECT * FROM video_assets WHERE content_id = 1;
```

## 현재 구현 상태

### ✅ 완료
- FastAPI 내부 upsert 엔드포인트
- Lambda API 호출 로직
- 파일명 → title 변환 로직

### 📝 메타데이터 생성 방식 (옵션 A - 현재 구현)
- **파일명**: `1_test_video.mp4`
- **title**: "Test Video" (slug를 사람이 읽게 변환)
- **description**: "Uploaded video: test_video"
- **age_rating**: "ALL"

## 최종 인프라 배포 시

1. Lambda 환경 변수 확인:
   - `CATALOG_API_BASE`: `https://api.matchacake.click/api` (또는 내부 엔드포인트)
   - `INTERNAL_TOKEN`: `formation-lap-internal-token-2024-secret-key`

2. FastAPI 환경 변수 확인:
   - `INTERNAL_TOKEN`: Lambda와 동일한 값

3. S3 업로드 테스트:
   ```bash
   aws s3 cp test_video.mp4 s3://<bucket>/videos/1_test_video.mp4
   ```

4. CloudWatch 로그 확인:
   ```bash
   aws logs tail /aws/lambda/formation-lap-video-processor --follow
   ```

## 문제 해결

### FastAPI 호출 실패 (DNS 해결 불가)
- **원인**: Lambda가 VPC 내부에 있어 외부 도메인 해결 불가
- **해결**: 
  - 옵션 1: NAT Gateway 확인 (이미 설정됨)
  - 옵션 2: 내부 Kubernetes 서비스 엔드포인트 사용
  - 옵션 3: 현재 상태 유지 (핵심 기능은 정상 동작)

### DB 연결 실패
- 로컬에서 테스트 시: `DB_HOST`를 실제 RDS Proxy로 설정
- 또는 SQLite 모드로 전환 (별도 설정 필요)
