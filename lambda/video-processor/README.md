# Video Processor Lambda

AWS Lambda 기반 비디오 처리 서비스

## 개요

Video Processor Lambda는 S3에 업로드된 비디오 파일을 자동으로 처리하는 서버리스 함수입니다. 
비디오 메타데이터 추출, 썸네일 생성, 데이터베이스 저장, 그리고 FastAPI를 통한 컨텐츠 메타데이터 업데이트를 수행합니다.

## 구조

```
Backend/lambda/video-processor/
├── app.py                    # Lambda 핸들러 및 비디오 처리 로직
├── Dockerfile                # Lambda 컨테이너 이미지 빌드
├── requirements.txt          # Python 의존성
├── PUSH_IMAGE.sh            # ECR 이미지 푸시 스크립트
├── API_INTEGRATION_GUIDE.md # FastAPI 연동 가이드
├── ARCHITECTURE.md          # 아키텍처 문서
└── README.md                # 이 파일
```

## 기능

### 1. 자동 트리거
- S3에 `videos/*.mp4` 파일 업로드 시 자동 실행
- S3 Event Notification을 통한 이벤트 기반 처리

### 2. 비디오 메타데이터 추출
- **FFprobe**를 사용하여 비디오 duration 추출
- 영상 길이 정보를 초 단위로 저장

### 3. 썸네일 생성
- **FFmpeg**를 사용하여 비디오에서 썸네일 추출
- 5초 지점의 프레임을 썸네일로 사용
- S3의 `thumbnails/` 경로에 저장

### 4. 데이터베이스 저장
- `video_assets` 테이블에 비디오 정보 저장
  - `content_id`: 파일명에서 추출 또는 자동 생성
  - `video_url`: S3 비디오 경로 (s3:// 형식)
  - `thumbnail_url`: S3 썸네일 경로 (s3:// 형식)
  - `duration`: 비디오 길이 (초)

### 5. FastAPI 연동
- 내부 upsert API를 호출하여 `contents` 테이블 업데이트
- 파일명에서 slug 추출하여 title 자동 생성
- `description`, `age_rating` 자동 설정

## 워크플로우

```
1. S3에 비디오 업로드
   └─> videos/{content_id}_{slug}.mp4
       예: videos/1_test_video.mp4

2. S3 Event Trigger
   └─> Lambda 함수 자동 실행

3. Lambda 처리
   ├─> S3에서 비디오 다운로드 (/tmp)
   ├─> FFprobe로 duration 추출
   ├─> FFmpeg로 썸네일 생성 (5초 지점)
   ├─> 썸네일을 S3 thumbnails/ 경로에 업로드
   ├─> FastAPI upsert API 호출
   │   └─> contents 테이블에 title/description/age_rating 저장
   └─> video_assets 테이블에 데이터 저장

4. 완료
   └─> CloudWatch 로그에 결과 기록
```

## 시작하기

### 로컬 개발

#### 1. 의존성 설치

```bash
cd /root/Backend/lambda/video-processor
pip install -r requirements.txt
```

#### 2. 환경 변수 설정

로컬 테스트를 위한 환경 변수:

```bash
export DB_HOST="your-rds-proxy-endpoint"
export DB_USER="admin"
export DB_PASSWORD="your-password"
export DB_NAME="ott_db"
export CATALOG_API_BASE="https://api.matchacake.click/api"
export INTERNAL_TOKEN="formation-lap-internal-token-2024-secret-key"
```

#### 3. 로컬 테스트

```python
# test_handler.py
import json
from app import handler

# S3 이벤트 시뮬레이션
event = {
    "Records": [{
        "s3": {
            "bucket": {"name": "your-bucket"},
            "object": {"key": "videos/1_test_video.mp4"}
        }
    }]
}

result = handler(event, None)
print(json.dumps(result, indent=2))
```

### Docker 빌드

#### 1. 이미지 빌드

```bash
cd /root/Backend/lambda/video-processor
docker build -t video-processor:latest .
```

#### 2. 로컬 테스트 (Docker)

```bash
docker run --rm \
  -e DB_HOST="your-rds-proxy-endpoint" \
  -e DB_USER="admin" \
  -e DB_PASSWORD="your-password" \
  -e DB_NAME="ott_db" \
  -e CATALOG_API_BASE="https://api.matchacake.click/api" \
  -e INTERNAL_TOKEN="your-token" \
  video-processor:latest
```

## AWS 배포

### 1. ECR 이미지 준비

```bash
cd /root/Backend/lambda/video-processor

# ECR 리포지토리 URL 확인
ECR_REPO=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-2.amazonaws.com/yuh-video-processor

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin $ECR_REPO

# 이미지 빌드
docker build -t video-processor:latest .

# 이미지 태그 및 푸시
docker tag video-processor:latest $ECR_REPO:v1
docker push $ECR_REPO:v1
```

또는 스크립트 사용:

```bash
bash PUSH_IMAGE.sh
```

### 2. Terraform으로 배포

Lambda 함수는 Terraform을 통해 자동 배포됩니다:

```bash
cd /root/Terraform/03-database
terraform init
terraform apply
```

### 3. S3 이벤트 설정

S3 버킷 알림은 Terraform에서 자동으로 설정됩니다:

```hcl
resource "aws_s3_bucket_notification" "video_trigger" {
  bucket = data.terraform_remote_state.infra.outputs.origin_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.video_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "videos/"
    filter_suffix       = ".mp4"
  }
}
```

## 환경 변수

### 필수 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DB_HOST` | RDS Proxy 엔드포인트 | `formation-lap-yuh-kor-rds-proxy.proxy-xxx.rds.amazonaws.com` |
| `DB_USER` | 데이터베이스 사용자명 | `admin` |
| `DB_PASSWORD` | 데이터베이스 비밀번호 | `your-password` |
| `DB_NAME` | 데이터베이스 이름 | `ott_db` |
| `CATALOG_API_BASE` | FastAPI 기본 URL | `https://api.matchacake.click/api` |
| `INTERNAL_TOKEN` | FastAPI 내부 인증 토큰 | `formation-lap-internal-token-2024-secret-key` |

### 선택적 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `FFMPEG_PATH` | FFmpeg 실행 경로 | `/usr/local/bin/ffmpeg` |
| `FFPROBE_PATH` | FFprobe 실행 경로 | `/usr/local/bin/ffprobe` |
| `BASTION_HOST` | Bastion 호스트 (SSH 터널링용) | 없음 |
| `BASTION_USER` | Bastion 사용자명 | `ec2-user` |
| `BASTION_SSH_KEY_SECRET` | Secrets Manager의 SSH 키 Secret 이름 | 없음 |
| `PROXY_ENDPOINT` | RDS Proxy 엔드포인트 (DB_HOST와 동일) | `DB_HOST` 값 사용 |
| `RDS_PORT` | RDS 포트 | `3306` |

## 파일명 형식

비디오 파일은 다음 형식을 따라야 합니다:

```
videos/{content_id}_{slug}.mp4
```

예시:
- `videos/1_test_video.mp4` → `content_id=1`, `title="Test Video"`
- `videos/123_my_awesome_movie.mp4` → `content_id=123`, `title="My Awesome Movie"`

### 파일명 파싱 규칙

1. **content_id 추출**: 파일명의 첫 번째 언더스코어(`_`) 앞의 숫자
2. **slug 추출**: 첫 번째 언더스코어 이후의 부분
3. **title 변환**: slug의 언더스코어/하이픈을 공백으로 변환하고 각 단어를 Capitalize

예시:
- `1_test_video.mp4` → `content_id=1`, `slug="test_video"`, `title="Test Video"`
- `42_my-movie-title.mp4` → `content_id=42`, `slug="my-movie-title"`, `title="My Movie Title"`

### content_id가 없는 경우

파일명에서 `content_id`를 추출할 수 없는 경우:
- `contents` 테이블에 새 레코드 생성 (AUTO_INCREMENT)
- 생성된 `id`를 `content_id`로 사용

## 데이터베이스 스키마

### video_assets 테이블

```sql
CREATE TABLE video_assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    video_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500) NOT NULL,
    duration INT NOT NULL,  -- 초 단위
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES contents(id)
);
```

### contents 테이블 (FastAPI를 통해 업데이트)

```sql
CREATE TABLE contents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    age_rating VARCHAR(10),
    like_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## FastAPI 연동

Lambda는 FastAPI의 내부 upsert 엔드포인트를 호출하여 `contents` 테이블을 업데이트합니다.

### API 엔드포인트

```
PUT /api/v1/contents/{content_id}/upsert-internal
```

### 요청 헤더

```
X-Internal-Token: {INTERNAL_TOKEN}
Content-Type: application/json
```

### 요청 본문

```json
{
  "title": "Test Video",
  "description": "Uploaded video: test_video",
  "age_rating": "ALL"
}
```

### 응답

```json
{
  "id": 1,
  "title": "Test Video",
  "age_rating": "ALL"
}
```

자세한 내용은 [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)를 참고하세요.

## 모니터링

### CloudWatch 로그

Lambda 함수의 로그는 CloudWatch Logs에 자동으로 저장됩니다:

```
/aws/lambda/{function-name}
```

예시:
```bash
aws logs tail /aws/lambda/formation-lap-video-processor --follow
```

### 주요 로그 메시지

- `영상 처리 시작: {key}` - 처리 시작
- `영상 다운로드 완료: {size} bytes ({size} MB)` - 다운로드 완료
- `영상 duration 추출 완료: {duration}초` - 메타데이터 추출 완료
- `썸네일 추출 완료: {size} bytes` - 썸네일 생성 완료
- `FastAPI upsert 호출 시작: {url}` - API 호출 시작
- `FastAPI upsert 성공: content_id={id}, title={title}` - API 호출 성공
- `video_assets 테이블에 등록 완료 (content_id: {id})` - DB 저장 완료
- `성공: {key} 등록 완료 (content_id: {id})` - 전체 처리 완료

### CloudWatch 메트릭

- `Invocations`: 함수 호출 횟수
- `Duration`: 실행 시간
- `Errors`: 오류 발생 횟수
- `Throttles`: 스로틀링 발생 횟수
- `ConcurrentExecutions`: 동시 실행 수

## 문제 해결

### 1. S3 접근 오류

**증상:**
```
AccessDenied: Access Denied
```

**해결 방법:**
- Lambda IAM 역할에 S3 읽기/쓰기 권한 확인
  ```json
  {
    "Effect": "Allow",
    "Action": [
      "s3:GetObject",
      "s3:PutObject",
      "s3:HeadObject"
    ],
    "Resource": "arn:aws:s3:::your-bucket/*"
  }
  ```
- VPC 엔드포인트 설정 확인 (VPC 내부에서 실행 시)
- 버킷 정책 확인

### 2. 데이터베이스 연결 실패

**증상:**
```
pymysql.Error: (2003, "Can't connect to MySQL server")
```

**해결 방법:**

1. **RDS Proxy 상태 확인**
   ```bash
   aws rds describe-db-proxies \
     --db-proxy-name formation-lap-yuh-kor-rds-proxy \
     --region ap-northeast-2
   ```

2. **보안 그룹 규칙 확인**
   - Lambda 보안 그룹에서 RDS Proxy 포트(3306) 허용 확인
   - RDS Proxy 보안 그룹에서 Lambda 보안 그룹 허용 확인

3. **VPC 설정 확인**
   - Lambda가 올바른 서브넷에 배포되었는지 확인
   - NAT Gateway 또는 VPC 엔드포인트 설정 확인

4. **비밀번호 확인**
   ```bash
   # Terraform 변수 확인
   cd /root/Terraform/03-database
   terraform output
   ```

자세한 내용은 [DB_CONNECTION_FIX.md](./DB_CONNECTION_FIX.md)를 참고하세요.

### 3. FFmpeg/FFprobe 실행 실패

**증상:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/usr/local/bin/ffmpeg'
```

**해결 방법:**
- Dockerfile에서 FFmpeg/FFprobe 설치 확인
- 환경 변수 `FFMPEG_PATH`, `FFPROBE_PATH` 확인
- 컨테이너 이미지 재빌드

### 4. FastAPI API 호출 실패

**증상:**
```
FastAPI 호출 중 네트워크 오류: Connection timeout
```

**해결 방법:**

1. **환경 변수 확인**
   ```bash
   aws lambda get-function-configuration \
     --function-name formation-lap-video-processor \
     --query 'Environment.Variables'
   ```

2. **네트워크 설정 확인**
   - Lambda가 VPC 내부에 있으면 NAT Gateway 경로 확인
   - 또는 Lambda를 VPC 밖으로 이동

3. **API 엔드포인트 확인**
   - `CATALOG_API_BASE` 값이 올바른지 확인
   - Ingress 설정 확인

4. **토큰 확인**
   - `INTERNAL_TOKEN`이 FastAPI와 일치하는지 확인
   - FastAPI 환경 변수 확인

5. **API 테스트**
   ```bash
   curl -X PUT "https://api.matchacake.click/api/v1/contents/1/upsert-internal" \
     -H "X-Internal-Token: your-token" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test","description":"Test","age_rating":"ALL"}'
   ```

### 5. 썸네일 생성 실패

**증상:**
```
subprocess.CalledProcessError: Command '['ffmpeg', ...]' returned non-zero exit status 1
```

**해결 방법:**
- 비디오 파일이 손상되었는지 확인
- FFmpeg 로그 확인 (stderr)
- 타임아웃 설정 확인 (현재 60초)
- 메모리 부족 확인 (현재 2048 MB)

### 6. 파일명 파싱 오류

**증상:**
```
ValueError: invalid literal for int() with base 10: 'test'
```

**해결 방법:**
- 파일명 형식 확인: `{content_id}_{slug}.mp4`
- content_id가 숫자인지 확인
- 언더스코어(`_`)가 포함되어 있는지 확인

### 7. 타임아웃 오류

**증상:**
```
Task timed out after 600.00 seconds
```

**해결 방법:**
- 비디오 파일 크기 확인
- Lambda 타임아웃 설정 증가 (최대 900초)
- 메모리 설정 증가 (더 빠른 처리)

## 성능 최적화

### 메모리 설정

현재 설정: `2048 MB`

비디오 파일 크기에 따라 조정:
- 작은 파일 (< 100MB): `1024 MB`
- 중간 파일 (100-500MB): `2048 MB` (현재)
- 큰 파일 (> 500MB): `3008 MB`

### 타임아웃 설정

현재 설정: `600 초` (10분)

처리 시간에 따라 조정:
- 일반 비디오: `300 초` (5분)
- 긴 비디오: `600 초` (10분, 현재)
- 매우 긴 비디오: `900 초` (15분, 최대)

### 동시 실행 제한

Lambda 동시 실행 수를 제한하여 데이터베이스 부하 방지:

```hcl
resource "aws_lambda_function" "video_processor" {
  # ...
  reserved_concurrent_executions = 5
}
```

## 보안

### IAM 권한

Lambda 함수는 다음 권한이 필요합니다:

- **S3**: `s3:GetObject`, `s3:PutObject`, `s3:HeadObject`, `s3:GetObjectTagging`
- **RDS**: 데이터베이스 연결 (VPC 내부)
- **Secrets Manager**: SSH 키 조회 (Bastion 사용 시)
- **VPC**: 네트워크 인터페이스 생성/삭제

### 네트워크 보안

- Lambda는 VPC 내부의 Private 서브넷에 배포
- RDS Proxy를 통해서만 데이터베이스 접근
- 보안 그룹으로 트래픽 제어

### 비밀 정보 관리

- 데이터베이스 비밀번호: Terraform 변수로 관리 (Sensitive)
- FastAPI 토큰: 환경 변수로 관리
- SSH 키: Secrets Manager에 저장 (Bastion 사용 시)

## 테스트

### 로컬 테스트

```bash
# 테스트 이벤트 생성
cat > test_event.json << EOF
{
  "Records": [{
    "s3": {
      "bucket": {"name": "test-bucket"},
      "object": {"key": "videos/1_test_video.mp4"}
    }
  }]
}
EOF

# Lambda 함수 테스트
python -c "
import json
from app import handler

with open('test_event.json') as f:
    event = json.load(f)
    
result = handler(event, None)
print(json.dumps(result, indent=2))
"
```

### AWS에서 테스트

```bash
# S3에 테스트 비디오 업로드
aws s3 cp test_video.mp4 s3://your-bucket/videos/1_test_video.mp4

# CloudWatch 로그 확인
aws logs tail /aws/lambda/formation-lap-video-processor --follow
```

### 데이터베이스 확인

```sql
-- video_assets 확인
SELECT * FROM video_assets WHERE content_id = 1;

-- contents 확인
SELECT * FROM contents WHERE id = 1;

-- 조인 쿼리 (FastAPI에서 사용)
SELECT 
    c.id,
    c.title,
    c.description,
    c.age_rating,
    va.video_url,
    va.thumbnail_url,
    va.duration
FROM contents c
LEFT JOIN video_assets va ON c.id = va.content_id
WHERE c.id = 1;
```

## 기술 스택

- **AWS Lambda**: 서버리스 컴퓨팅 (Python 3.11, Container Image)
- **Amazon S3**: 영상 파일 저장소
- **Amazon ECR**: Docker 이미지 저장소
- **Aurora MySQL**: 관계형 데이터베이스
- **RDS Proxy**: DB 연결 관리
- **FFmpeg/FFprobe**: 영상 처리 도구
- **Terraform**: Infrastructure as Code
- **FastAPI**: 백엔드 API (내부 연동)

## 참고 문서

- [API 연동 가이드](./API_INTEGRATION_GUIDE.md) - FastAPI 연동 상세 가이드
- [아키텍처 문서](./ARCHITECTURE.md) - 시스템 아키텍처 설명
- [빠른 설정 가이드](./QUICK_SETUP.md) - 빠른 시작 가이드
- [DB 연결 문제 해결](./DB_CONNECTION_FIX.md) - 데이터베이스 연결 문제 해결

## 라이선스

프로젝트 라이선스를 참고하세요.
