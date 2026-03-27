# TMDB API 연동 가이드

## 개요

Lambda 함수가 TMDB API를 사용하여 영상 정보를 가져와서 `contents` 테이블에 저장합니다.

## 기능

1. **영상 검색**: 파일명의 slug를 기반으로 TMDB에서 영화 검색
2. **상세 정보 가져오기**: 제목, 설명, 연령 등급 가져오기
3. **자동 저장**: 가져온 정보로 `contents` 테이블 자동 저장

## TMDB API 키 발급

1. [TMDB 웹사이트](https://www.themoviedb.org/)에 가입
2. [API 설정 페이지](https://www.themoviedb.org/settings/api)에서 API 키 발급
3. API 키를 환경 변수에 설정

## 설정 방법

### 1. Lambda 환경 변수 설정

```bash
aws lambda update-function-configuration \
  --function-name formation-lap-video-processor \
  --environment "Variables={
    TMDB_API_KEY=your_tmdb_api_key_here,
    ...
  }" \
  --region ap-northeast-2
```

### 2. Terraform으로 설정 (권장)

`terraform.tfvars` 파일에 추가:

```hcl
tmdb_api_key = "your_tmdb_api_key_here"
```

그리고 Terraform apply:

```bash
cd /root/Terraform/03-database
terraform apply
```

## 동작 방식

### 파일명 형식
```
videos/{content_id}_{movie_slug}.mp4
```

예시:
- `videos/1_inception.mp4` → TMDB에서 "inception" 검색
- `videos/2_the_matrix.mp4` → TMDB에서 "the matrix" 검색

### 처리 순서

1. **파일명에서 slug 추출**
   - `1_inception.mp4` → `inception`

2. **TMDB 검색**
   - 검색어: `inception`
   - API: `GET /search/movie?query=inception`

3. **상세 정보 가져오기**
   - 첫 번째 검색 결과의 영화 ID 사용
   - API: `GET /movie/{id}?append_to_response=release_dates`

4. **연령 등급 변환**
   - 한국(KR): `12`, `15`, `18` → `12+`, `15+`, `18+`
   - 미국(US): `PG`, `PG-13`, `R`, `NC-17` → 변환
   - 기본값: `ALL`

5. **contents 테이블 저장**
   - `title`: TMDB 제목
   - `description`: TMDB 설명 (overview)
   - `age_rating`: 변환된 연령 등급

## 폴백 로직

TMDB API 호출이 실패하면:
- 파일명에서 title 추출 (기존 방식)
- description: "Uploaded video: {slug}"
- age_rating: "ALL"

## 예시

### 입력
```
파일명: videos/1_inception.mp4
```

### TMDB API 호출
```python
# 검색
GET https://api.themoviedb.org/3/search/movie?api_key=xxx&query=inception

# 상세 정보
GET https://api.themoviedb.org/3/movie/27205?api_key=xxx&append_to_response=release_dates
```

### 결과
```json
{
  "title": "인셉션",
  "description": "타인의 꿈에 들어가 생각을 훔치는 특수 보안요원 코브...",
  "age_rating": "12+"
}
```

### DB 저장
```sql
INSERT INTO contents (id, title, description, age_rating, like_count)
VALUES (1, '인셉션', '타인의 꿈에 들어가 생각을 훔치는 특수 보안요원 코브...', '12+', 0);
```

## 테스트

### 1. TMDB API 키 확인
```bash
aws lambda get-function-configuration \
  --function-name formation-lap-video-processor \
  --query 'Environment.Variables.TMDB_API_KEY' \
  --region ap-northeast-2
```

### 2. S3에 테스트 비디오 업로드
```bash
# 파일명: {content_id}_{movie_slug}.mp4
aws s3 cp test_video.mp4 s3://<bucket>/videos/1_inception.mp4
```

### 3. CloudWatch 로그 확인
```bash
aws logs tail /aws/lambda/formation-lap-video-processor --follow
```

**성공 로그 예시:**
```
[INFO] TMDB 검색 시작: inception
[INFO] TMDB 정보 가져오기 성공: 인셉션, age_rating: 12+
[INFO] TMDB 정보 사용: 인셉션, age_rating: 12+
```

## 주의사항

1. **API 키 보안**: TMDB API 키는 민감 정보이므로 환경 변수로 관리
2. **API 제한**: TMDB API는 요청 제한이 있음 (초당 40회)
3. **검색 정확도**: 파일명의 slug가 정확할수록 검색 결과가 정확함
4. **언어 설정**: 한국어 결과를 우선 사용 (`language=ko-KR`)

## 문제 해결

### TMDB 검색 결과 없음
- 파일명의 slug를 더 명확하게 변경
- 예: `inception` → `inception_2010`

### API 호출 실패
- API 키 확인
- 네트워크 연결 확인 (Lambda가 인터넷 접근 가능한지)
- API 제한 확인

### 연령 등급이 "ALL"로만 저장됨
- TMDB에 해당 국가의 등급 정보가 없을 수 있음
- 한국/미국 등급 정보가 있는 영화만 등급이 설정됨
