# 최종 체크리스트

## ✅ 완료된 작업

### 1. Lambda 함수 구현
- [x] FFmpeg/FFprobe 설치 및 동작 확인
- [x] video_assets 테이블 직접 저장 (API 호출 없이)
- [x] contents 테이블 저장 (TMDB 정보 사용)
- [x] TMDB API 연동 (한국 등급만)
- [x] 폴백 로직 (FastAPI 실패 시 DB 직접 저장)

### 2. FastAPI 구현
- [x] 내부 upsert 엔드포인트 (`/api/v1/contents/{id}/upsert-internal`)
- [x] 비디오 목록 조회 API (`/videos/search/`)
- [x] 비디오 상세 조회 API (`/videos/watch/{id}`)
- [x] 썸네일 URL 포함하여 응답

### 3. 인프라 설정
- [x] Lambda 함수 배포
- [x] Lambda 환경 변수 설정
- [x] DNS 문제 해결 시도 (내부 엔드포인트)
- [x] S3 Event Trigger 설정

## ⚠️ 확인 필요 사항

### 1. Lambda 이미지 업데이트
현재 코드 변경사항이 Lambda에 반영되었는지 확인:

```bash
# 최신 코드로 이미지 재빌드 및 배포 필요
cd /root/Backend/lambda/video-processor
docker build -t yuh-video-processor:v1 .
# ECR 푸시 및 Lambda 업데이트
```

**변경사항:**
- TMDB API 연동 추가
- 한국 등급만 사용하도록 수정
- 썸네일 URL 포함

### 2. TMDB API 키 설정
```bash
# Lambda 환경 변수에 TMDB_API_KEY가 설정되어 있는지 확인
aws lambda get-function-configuration \
  --function-name formation-lap-video-processor \
  --query 'Environment.Variables.TMDB_API_KEY' \
  --region ap-northeast-2
```

**설정되지 않았다면:**
```bash
aws lambda update-function-configuration \
  --function-name formation-lap-video-processor \
  --environment "Variables={
    TMDB_API_KEY=your_tmdb_api_key_here,
    ...
  }" \
  --region ap-northeast-2
```

### 3. 최종 End-to-End 테스트
```bash
# 1. S3에 테스트 비디오 업로드
aws s3 cp test_video.mp4 s3://<bucket>/videos/3_test_movie.mp4

# 2. CloudWatch 로그 확인
aws logs tail /aws/lambda/formation-lap-video-processor --follow

# 3. FastAPI로 조회 테스트
curl http://api.matchacake.click/videos/search/
# 또는
curl http://localhost:8000/videos/search/
```

**확인 사항:**
- [ ] Lambda 실행 성공
- [ ] video_assets 테이블 저장 확인
- [ ] contents 테이블 저장 확인 (TMDB 정보 또는 파일명 기반)
- [ ] FastAPI 조회 API 정상 동작
- [ ] 썸네일 URL 포함하여 응답

## 📋 제출 전 최종 확인

### 코드 상태
- [x] Lambda 코드 완성 (TMDB 연동 포함)
- [x] FastAPI 코드 완성 (썸네일 URL 포함)
- [ ] Lambda 이미지 최신 코드로 배포됨
- [ ] TMDB API 키 설정됨

### 테스트
- [ ] S3 업로드 → Lambda 실행 테스트
- [ ] DB 저장 확인 (video_assets + contents)
- [ ] FastAPI 조회 테스트
- [ ] 프론트엔드 연동 테스트 (선택)

### 문서
- [x] README.md (Lambda)
- [x] API 가이드 (프론트엔드용)
- [x] 워크플로우 설명

## 🎯 즉시 할 일 (제출 전 필수)

### 1. Lambda 이미지 재배포 (TMDB 코드 반영)
```bash
cd /root/Backend/lambda/video-processor
bash PUSH_IMAGE.sh
# 또는
REGION="ap-northeast-2"
ACCOUNT_ID="404457776061"
REPO_NAME="yuh-video-processor"
IMAGE_TAG="latest-$(date +%Y%m%d-%H%M%S)"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

docker build -t yuh-video-processor:v1 .
docker tag yuh-video-processor:v1 ${ECR_URI}
docker push ${ECR_URI}

aws lambda update-function-code \
  --function-name formation-lap-video-processor \
  --image-uri ${ECR_URI} \
  --region ap-northeast-2
```

### 2. TMDB API 키 설정 (선택사항)
TMDB API 키가 없으면 파일명 기반으로 동작 (폴백)

### 3. 최종 테스트 1회
```bash
# S3 업로드
aws s3 cp test_video.mp4 s3://<bucket>/videos/4_final_test.mp4

# 로그 확인
aws logs tail /aws/lambda/formation-lap-video-processor --follow

# API 테스트
curl http://api.matchacake.click/videos/search/
```

## ✅ 완료 기준

다음이 모두 확인되면 완료:

1. ✅ Lambda 코드 완성
2. ✅ FastAPI 코드 완성
3. ⚠️ Lambda 이미지 최신 코드로 배포
4. ⚠️ 최종 테스트 1회 성공
5. ✅ 프론트엔드 API 가이드 제공

## 📝 제출용 요약

### 구현 완료
- ✅ video_assets: Lambda 함수로 직접 저장
- ✅ contents: FastAPI API로 저장 (TMDB 정보 사용)
- ✅ 조회 API: 프론트엔드에서 바로 사용 가능

### 핵심 기능
- ✅ S3 업로드 → 자동 처리
- ✅ 썸네일 자동 생성
- ✅ TMDB 영상 정보 자동 가져오기
- ✅ 프론트엔드 API 제공
