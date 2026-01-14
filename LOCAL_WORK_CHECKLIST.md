# 로컬 작업 체크리스트 (제출용)

## 현재 상태 확인 ✅

### 1. FastAPI 내부 Upsert 엔드포인트
- ✅ `/root/Backend/app/api/v1/routes/contents_internal.py` 존재
- ✅ `PUT /api/v1/contents/{content_id}/upsert-internal` 구현됨
- ⚠️ FastAPI main 앱에 router 등록 확인 필요

### 2. Lambda 코드
- ✅ `upsert_contents_via_api()` 함수 구현됨
- ✅ 파일명에서 slug 추출 → title 변환 로직 있음
- ✅ FastAPI 호출 로직 있음

### 3. 메타데이터 생성 방식
- ✅ **옵션 A (현재 구현)**: 파일명에서 title 생성
  - 파일명: `1_test_video.mp4` → title: "Test Video"
  - description: "Uploaded video: test_video"
  - age_rating: "ALL"

## 작업 순서

### Step 1: FastAPI 설정 확인 및 수정 (로컬)

#### 1-1. FastAPI main 앱 찾기 및 router 등록
```bash
# FastAPI 앱 파일 찾기
find /root/Backend -name "*.py" -type f | xargs grep -l "FastAPI\|from fastapi import FastAPI" | head -5
```

#### 1-2. contents_internal router 등록 확인
```python
# main.py 또는 app.py에 추가 필요:
from app.api.v1.routes import contents_internal
app.include_router(contents_internal.router, prefix="/api/v1")
```

#### 1-3. config.py에 INTERNAL_TOKEN 추가
```python
# app/core/config.py
class Settings:
    INTERNAL_TOKEN: str = os.getenv("INTERNAL_TOKEN", "formation-lap-internal-token-2024-secret-key")
```

### Step 2: 로컬에서 FastAPI 실행 및 테스트

#### 2-1. 환경 변수 설정
```bash
export DB_HOST="localhost"  # 또는 SQLite 사용
export DB_USER="admin"
export DB_PASSWORD="test1234"
export DB_NAME="ott_db"
export INTERNAL_TOKEN="formation-lap-internal-token-2024-secret-key"
```

#### 2-2. FastAPI 실행
```bash
cd /root/Backend
uvicorn main:app --host 0.0.0.0 --port 8000
# 또는
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 2-3. 내부 Upsert API 테스트
```bash
cd /root/Backend
export API_BASE="http://localhost:8000/api"
export INTERNAL_TOKEN="formation-lap-internal-token-2024-secret-key"
./scripts/test_internal_api.sh 1
```

**예상 응답:**
```json
{
  "id": 1,
  "title": "Test Video",
  "age_rating": "ALL"
}
```

### Step 3: Lambda 코드 검증 (로컬)

#### 3-1. Lambda 핸들러 로직 확인
- ✅ `extract_slug_from_filename()` - 파일명에서 slug 추출
- ✅ `slug_to_title()` - slug를 title로 변환
- ✅ `upsert_contents_via_api()` - FastAPI 호출

#### 3-2. 로컬에서 Lambda 로직 테스트
```python
# test_lambda_local.py
import os
os.environ["CATALOG_API_BASE"] = "http://localhost:8000/api"
os.environ["INTERNAL_TOKEN"] = "formation-lap-internal-token-2024-secret-key"

from app import extract_slug_from_filename, slug_to_title, upsert_contents_via_api

# 테스트
key = "videos/1_test_video.mp4"
slug = extract_slug_from_filename(key)  # "test_video"
title = slug_to_title(slug)  # "Test Video"

# FastAPI 호출 테스트
upsert_contents_via_api(1, key)
```

### Step 4: 전체 워크플로우 테스트 (로컬 SQLite)

#### 4-1. SQLite 모드로 FastAPI 실행
```python
# SQLite 사용 시 config 수정
DATABASE_URL = "sqlite:///./test.db"
```

#### 4-2. 수동으로 Lambda 로직 실행
```python
# simulate_lambda.py
# 1. S3 이벤트 시뮬레이션
event = {
    "Records": [{
        "s3": {
            "bucket": {"name": "test-bucket"},
            "object": {"key": "videos/1_test_video.mp4"}
        }
    }]
}

# 2. Lambda 핸들러 실행 (로컬 환경)
from app import handler
result = handler(event, None)
```

#### 4-3. DB 확인
```sql
-- contents 테이블 확인
SELECT * FROM contents WHERE id = 1;

-- video_assets 테이블 확인
SELECT * FROM video_assets WHERE content_id = 1;
```

### Step 5: 최종 인프라 배포 및 테스트

#### 5-1. Terraform 배포 (필요 시)
```bash
cd /root/Terraform/03-database
terraform apply
```

#### 5-2. Lambda 이미지 업데이트 (필요 시)
```bash
cd /root/Backend/lambda/video-processor
bash PUSH_IMAGE.sh
aws lambda update-function-code \
  --function-name formation-lap-video-processor \
  --image-uri <ECR_URI>
```

#### 5-3. S3에 테스트 비디오 업로드
```bash
aws s3 cp test_video.mp4 s3://<bucket>/videos/1_test_video.mp4
```

#### 5-4. CloudWatch 로그 확인
```bash
aws logs tail /aws/lambda/formation-lap-video-processor --follow
```

#### 5-5. DB 최종 확인
```sql
SELECT * FROM contents WHERE id = 1;
SELECT * FROM video_assets WHERE content_id = 1;
```

## 핵심 포인트

### ✅ 완료된 부분
1. FastAPI 내부 upsert 엔드포인트 구현됨
2. Lambda API 호출 로직 구현됨
3. 파일명 → title 변환 로직 구현됨

### ⚠️ 확인 필요
1. FastAPI main 앱에 router 등록 여부
2. config.py에 INTERNAL_TOKEN 설정 여부
3. 로컬에서 FastAPI 실행 가능 여부

### 🎯 제출용 증빙 자료
1. S3 업로드 → Lambda 실행 로그 (CloudWatch)
2. DB 쿼리 결과 (contents + video_assets)
3. FastAPI 내부 upsert API 호출 성공 로그

## 빠른 시작 (로컬)

```bash
# 1. FastAPI 실행
cd /root/Backend
export INTERNAL_TOKEN="formation-lap-internal-token-2024-secret-key"
uvicorn main:app --host 0.0.0.0 --port 8000

# 2. 다른 터미널에서 테스트
export API_BASE="http://localhost:8000/api"
export INTERNAL_TOKEN="formation-lap-internal-token-2024-secret-key"
./scripts/test_internal_api.sh 1
```
