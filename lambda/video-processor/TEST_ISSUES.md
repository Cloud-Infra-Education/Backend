# 테스트 중 발견된 문제 및 해결 방법

## 발견된 문제

### 1. 타임아웃 발생 (60초)
**증상:**
- Lambda 함수가 60초 내에 완료되지 않음
- Status: timeout

**원인:**
- 영상 파일이 너무 큼
- FFmpeg/FFprobe 처리 시간이 오래 걸림
- VPC 내에서 S3 접근이 느릴 수 있음

**해결:**
- Lambda timeout을 60초 → 300초 (5분)로 증가
- Memory를 1024MB → 2048MB로 증가 (FFmpeg 성능 향상)

### 2. 파일 경로 불일치
**증상:**
- 로그에 `uploads/1_test_video.mp4`로 표시됨
- Terraform 설정은 `videos/`로 되어 있음

**해결 방법:**
1. **옵션 1**: S3에 `videos/` 경로로 업로드 (권장)
   ```bash
   aws s3 cp video.mp4 s3://{bucket}/videos/1_test.mp4
   ```

2. **옵션 2**: Terraform 설정을 `uploads/`로 변경
   ```hcl
   filter_prefix = "uploads/"
   ```

### 3. 로깅 개선
**추가된 로그:**
- S3 버킷 및 키 정보
- 영상 다운로드 시작/완료 (파일 크기)
- FFprobe 메타데이터 추출 시작/완료
- 썸네일 추출 시작/완료 (파일 크기)
- 에러 상세 정보

## 수정 사항

### Lambda 함수 코드 (`app.py`)
- 각 단계별 상세 로깅 추가
- FFmpeg 타임아웃 처리 개선
- 에러 메시지 상세화

### Terraform 설정 (`main.tf`)
- `timeout`: 60 → 300초
- `memory_size`: 1024 → 2048 MB

## 재배포 방법

### 1. Lambda 함수 코드 업데이트
```bash
cd Backend/lambda/video-processor

# Docker 이미지 재빌드
docker build -t yuh-video-processor:v1 .

# ECR에 푸시
docker tag yuh-video-processor:v1 \
    404457776061.dkr.ecr.ap-northeast-2.amazonaws.com/yuh-video-processor:v1
docker push 404457776061.dkr.ecr.ap-northeast-2.amazonaws.com/yuh-video-processor:v1
```

### 2. Terraform 적용
```bash
cd ../../Terraform
terraform apply
```

## 재테스트 방법

### 올바른 경로로 업로드
```bash
# videos/ 경로로 업로드 (중요!)
aws s3 cp test-video.mp4 s3://{bucket}/videos/1_test_$(date +%s).mp4
```

### 로그 확인
```bash
aws logs tail /aws/lambda/formation-lap-video-processor --follow
```

### 확인할 로그
```
영상 처리 시작: videos/...
S3 버킷: ..., 키: videos/...
영상 다운로드 시작: ...
영상 다운로드 완료: ... bytes
FFprobe로 영상 메타데이터 추출 시작
영상 duration 추출 완료: ...초
썸네일 추출 시작: ...
썸네일 추출 완료: ... bytes
DB 연결 시도: ...
DB 연결 성공
contents 테이블에 등록 완료 (content_id: ...)
video_assets 테이블에 등록 완료 (content_id: ...)
성공: videos/... 등록 완료
```

## 주의사항

1. **파일 경로**: 반드시 `videos/`로 시작해야 함
2. **파일 확장자**: `.mp4`여야 함
3. **파일 크기**: 너무 큰 파일은 타임아웃 발생 가능
4. **VPC 설정**: Lambda가 VPC 내에 있어서 S3 접근이 느릴 수 있음
