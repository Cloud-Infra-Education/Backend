# Video Processor Lambda 아키텍처 및 기술 스택

## 개요

S3에 영상 파일이 업로드되면 자동으로 트리거되어 영상 메타데이터를 추출하고, 썸네일을 생성한 후 Aurora MySQL 데이터베이스에 저장하는 서버리스 함수입니다.

## 아키텍처 다이어그램

```
S3 (videos/*.mp4 업로드)
    ↓
S3 Bucket Notification (자동 트리거)
    ↓
Lambda Function (video-processor)
    ├─ S3에서 영상 다운로드
    ├─ FFprobe로 duration 추출
    ├─ FFmpeg로 썸네일 생성
    ├─ S3에 썸네일 업로드
    └─ RDS Proxy → Aurora MySQL
        ├─ contents 테이블에 메타데이터 저장
        └─ video_assets 테이블에 영상 정보 저장
```

## 기술 스택

### 1. AWS Lambda (서버리스 컴퓨팅)

**역할:**
- S3 이벤트에 반응하여 영상 처리 작업 수행
- 서버 관리 없이 자동 스케일링

**구성:**
- **Runtime**: Python 3.11 (Docker Container Image)
- **Package Type**: Container Image (ECR 사용)
- **Memory**: 1024 MB
- **Timeout**: 60초
- **VPC Configuration**: Private 서브넷에 배포하여 RDS Proxy 접근

**주요 기능:**
- S3 이벤트 기반 자동 트리거
- 영상 다운로드 및 처리
- DB 연결 및 데이터 저장

### 2. Amazon S3 (Simple Storage Service)

**역할:**
- 원본 영상 파일 저장
- 생성된 썸네일 이미지 저장

**구성:**
- **Bucket**: 영상 원본 저장소
- **Public Access**: 차단 (보안)
- **Event Notification**: 
  - 트리거 경로: `videos/` prefix
  - 파일 형식: `.mp4` suffix
  - 이벤트: `s3:ObjectCreated:*`

**저장 구조:**
```
s3://bucket/
  ├── videos/
  │   └── {content_id}_{timestamp}.mp4  (원본 영상)
  └── thumbnails/
      └── thumb_{filename}.jpg  (생성된 썸네일)
```

### 3. Amazon ECR (Elastic Container Registry)

**역할:**
- Lambda 함수용 Docker 이미지 저장 및 관리

**구성:**
- **Repository**: `yuh-video-processor`
- **Image Tag**: `v1`
- **Image Type**: Container Image (Lambda용)

**이미지 구성:**
- Base Image: `public.ecr.aws/lambda/python:3.11`
- 추가 패키지: FFmpeg, FFprobe (정적 바이너리)
- Python 라이브러리: pymysql, boto3

### 4. FFmpeg / FFprobe (영상 처리)

**역할:**
- 영상 메타데이터 추출 (duration)
- 썸네일 이미지 생성

**구현 방식:**
- **FFprobe**: 영상 duration 추출
  ```bash
  ffprobe -v error -show_entries format=duration -of json {video_file}
  ```
- **FFmpeg**: 5초 지점에서 썸네일 추출
  ```bash
  ffmpeg -y -i {video_file} -ss 00:00:05 -vframes 1 {thumbnail_file}
  ```

**설치 방법:**
- Docker 이미지 빌드 시 정적 바이너리 다운로드
- `johnvansickle.com/ffmpeg`에서 제공하는 정적 빌드 사용

### 5. Aurora MySQL (관계형 데이터베이스)

**역할:**
- 영상 메타데이터 저장
- 영상 자산 정보 저장

**테이블 구조:**

**contents 테이블:**
```sql
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- title (VARCHAR(255))
- description (TEXT)
- age_rating (VARCHAR(10))
- like_count (INT, DEFAULT 0)
```

**video_assets 테이블:**
```sql
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- content_id (INT, FOREIGN KEY → contents.id)
- video_url (VARCHAR(500))  # S3 URI
- thumbnail_url (VARCHAR(500))  # S3 URI
- duration (INT)  # 초 단위
```

### 6. RDS Proxy (데이터베이스 연결 관리)

**역할:**
- Lambda 함수의 DB 연결 풀링
- 연결 관리 최적화 및 안정성 향상

**장점:**
- 연결 재사용으로 성능 향상
- 연결 수 제한 관리
- 자동 failover 지원

### 7. Amazon VPC (Virtual Private Cloud)

**역할:**
- Lambda 함수를 Private 서브넷에 배포
- RDS Proxy와의 안전한 통신

**구성:**
- **Subnet**: Private EKS 서브넷 사용
- **Security Group**: RDS Proxy 접근 허용
- **Network Isolation**: Public 인터넷과 격리

### 8. IAM (Identity and Access Management)

**역할:**
- Lambda 함수 실행 권한 관리
- 리소스 접근 권한 제어

**권한 구성:**

**기본 역할:**
- `AWSLambdaVPCAccessExecutionRole`: VPC 내 리소스 접근

**커스텀 정책:**
- **S3 권한:**
  - `s3:GetObject`: 영상 다운로드
  - `s3:PutObject`: 썸네일 업로드
  - `s3:HeadObject`: 메타데이터 조회
  - `s3:GetObjectTagging`: 태그 정보 조회
- **Secrets Manager 권한:**
  - `secretsmanager:GetSecretValue`: 시크릿 조회 (필요시)

### 9. CloudWatch Logs (로깅 및 모니터링)

**역할:**
- Lambda 함수 실행 로그 수집
- 에러 추적 및 디버깅

**로깅 정보:**
- 환경 변수 확인
- 영상 처리 시작/완료
- DB 연결 상태
- 각 단계별 처리 결과
- 에러 메시지 및 스택 트레이스

### 10. Terraform (Infrastructure as Code)

**역할:**
- 인프라 자동화 및 관리
- 재현 가능한 인프라 구성

**생성 리소스:**
- Lambda 함수
- IAM 역할 및 정책
- S3 버킷 알림 설정
- Lambda 권한 설정

**모듈 구조:**
```
Terraform/modules/s3/
  ├── main.tf          # Lambda 함수, S3 알림
  ├── iam-role.tf      # IAM 역할 및 정책
  ├── variables.tf     # 입력 변수
  └── outputs.tf      # 출력 값
```

## 데이터 흐름

### 1. 영상 업로드
```
사용자/시스템
    ↓
S3 버킷 (videos/{content_id}_{timestamp}.mp4)
```

### 2. 자동 트리거
```
S3 Bucket Notification
    ↓
Lambda Function (자동 실행)
```

### 3. 영상 처리
```
Lambda Function
    ├─ S3에서 영상 다운로드 (/tmp)
    ├─ FFprobe로 duration 추출
    ├─ FFmpeg로 썸네일 생성 (5초 지점)
    └─ S3에 썸네일 업로드 (thumbnails/)
```

### 4. 메타데이터 추출
```
S3 객체 메타데이터/태그
    ├─ title
    ├─ description
    ├─ age_rating
    └─ like_count

파일명 파싱
    └─ content_id (형식: {content_id}_{timestamp}.mp4)
```

### 5. 데이터베이스 저장
```
RDS Proxy
    ↓
Aurora MySQL
    ├─ contents 테이블: 메타데이터 저장
    └─ video_assets 테이블: 영상 정보 저장
```

## 보안 고려사항

### 1. 네트워크 보안
- Lambda 함수를 Private 서브넷에 배포
- Security Group으로 접근 제어
- Public 인터넷 접근 차단

### 2. 데이터 보안
- S3 버킷 Public Access 차단
- DB 비밀번호는 환경 변수로 관리 (Terraform)
- IAM 최소 권한 원칙 적용

### 3. 접근 제어
- IAM 역할 기반 권한 관리
- 리소스별 세분화된 권한 설정

## 성능 최적화

### 1. 연결 풀링
- RDS Proxy를 통한 DB 연결 재사용
- 연결 오버헤드 감소

### 2. 비동기 처리
- S3 이벤트 기반 비동기 실행
- 사용자 요청과 분리된 백그라운드 처리

### 3. 리소스 할당
- Lambda Memory: 1024 MB (FFmpeg 처리에 충분)
- Timeout: 60초 (대용량 영상 처리 고려)

## 확장성

### 1. 자동 스케일링
- Lambda 함수는 자동으로 동시 실행 수 증가
- S3 업로드 수에 따라 자동 확장

### 2. 처리 용량
- 동시에 여러 영상 처리 가능
- 각 Lambda 인스턴스는 독립적으로 실행

## 모니터링 및 로깅

### 1. CloudWatch Logs
- 모든 실행 로그 자동 수집
- 에러 추적 및 디버깅

### 2. 로그 레벨
- INFO: 정상 처리 흐름
- WARNING: 비정상 상황 (기본값 사용 등)
- ERROR: 처리 실패

## 에러 처리

### 1. 재시도 메커니즘
- Lambda 기본 재시도 정책 활용
- 실패 시 CloudWatch Logs에 기록

### 2. 예외 처리
- DB 연결 실패 시 명확한 에러 메시지
- 영상 처리 실패 시 로그 기록
- 임시 파일 자동 정리 (finally 블록)

## 배포 프로세스

### 1. Docker 이미지 빌드
```bash
docker build -t yuh-video-processor:v1 .
```

### 2. ECR에 푸시
```bash
docker push {ECR_URI}/yuh-video-processor:v1
```

### 3. Terraform 적용
```bash
terraform apply
```

### 4. 자동 배포
- Terraform이 Lambda 함수 생성/업데이트
- S3 알림 자동 설정
- IAM 권한 자동 구성

## 주요 파일 구조

```
Backend/lambda/video-processor/
  ├── app.py              # Lambda 핸들러 함수
  ├── Dockerfile          # Docker 이미지 빌드 설정
  ├── requirements.txt    # Python 의존성
  ├── PUSH_IMAGE.sh       # ECR 푸시 스크립트
  └── ARCHITECTURE.md     # 이 문서
```

## 기술 선택 이유

### 1. Lambda (서버리스)
- **이유**: 영상 업로드가 불규칙적이므로 서버리스가 적합
- **장점**: 사용한 만큼만 비용 지불, 자동 스케일링

### 2. RDS Proxy
- **이유**: Lambda의 짧은 실행 시간과 연결 관리 최적화
- **장점**: 연결 풀링, 자동 failover

### 3. FFmpeg (정적 바이너리)
- **이유**: Lambda 환경에 FFmpeg 설치 필요
- **장점**: 의존성 없이 독립 실행 가능

### 4. Container Image
- **이유**: FFmpeg 등 외부 바이너리 포함 필요
- **장점**: 모든 의존성을 이미지에 포함

### 5. VPC 배포
- **이유**: RDS Proxy는 Private 네트워크에 위치
- **장점**: 보안 강화, 네트워크 격리
