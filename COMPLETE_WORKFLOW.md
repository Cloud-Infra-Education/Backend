# 전체 워크플로우 확인

## ✅ 현재 구현 상태

### 1. 영상 업로드 → Lambda 실행 → DB 저장

#### Step 1: S3에 영상 업로드
```bash
aws s3 cp video.mp4 s3://<bucket>/videos/1_inception.mp4
```

#### Step 2: Lambda 자동 실행
- S3 Event Trigger → Lambda 함수 실행
- FFprobe로 duration 추출
- FFmpeg로 썸네일 생성
- S3에 썸네일 업로드

#### Step 3: DB 저장 (Lambda에서 직접)
```sql
-- video_assets 테이블 저장 (Lambda가 직접 INSERT)
INSERT INTO video_assets (content_id, video_url, thumbnail_url, duration)
VALUES (1, 's3://bucket/videos/1_inception.mp4', 's3://bucket/thumbnails/thumb_1_inception.jpg', 8880);

-- contents 테이블 저장 (TMDB 정보 또는 파일명 기반)
INSERT INTO contents (id, title, description, age_rating, like_count)
VALUES (1, '인셉션', '타인의 꿈에 들어가 생각을 훔치는...', '12+', 0);
```

**✅ 완료**: Lambda가 두 테이블 모두 DB에 직접 저장

### 2. FastAPI로 데이터 조회 → 프론트엔드 표시

#### API 엔드포인트 확인

**✅ 비디오 목록 조회 (contents + video_assets 조인)**
```http
GET /videos/search/
GET /videos/search/?q=검색어
```

**응답 예시:**
```json
{
  "query": null,
  "count": 1,
  "videos": [
    {
      "id": 1,
      "title": "인셉션",
      "description": "타인의 꿈에 들어가 생각을 훔치는...",
      "age_rating": "12+",
      "like_count": 0,
      "video_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/videos/1_inception.mp4",
      "duration": 8880
    }
  ]
}
```

**✅ 비디오 상세 조회**
```http
GET /videos/watch/{video_id}
```

**응답 예시:**
```json
{
  "video": {
    "id": 1,
    "title": "인셉션",
    "description": "타인의 꿈에 들어가 생각을 훔치는...",
    "age_rating": "12+",
    "like_count": 0,
    "video_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/videos/1_inception.mp4",
    "duration": 8880
  }
}
```

## 전체 워크플로우

```
1. 사용자가 S3에 영상 업로드
   ↓
2. S3 Event → Lambda 함수 자동 실행
   ↓
3. Lambda 처리:
   - FFprobe: duration 추출
   - FFmpeg: 썸네일 생성
   - S3: 썸네일 업로드
   - TMDB API: 영상 정보 가져오기 (선택)
   ↓
4. DB 저장 (Lambda가 직접):
   - video_assets 테이블: video_url, thumbnail_url, duration
   - contents 테이블: title, description, age_rating
   ↓
5. 프론트엔드가 FastAPI 호출:
   GET /videos/search/
   ↓
6. FastAPI가 DB 조회:
   SELECT c.*, va.video_url, va.thumbnail_url, va.duration
   FROM contents c
   LEFT JOIN video_assets va ON c.id = va.content_id
   ↓
7. 프론트엔드에 JSON 응답:
   - 비디오 목록 표시
   - 썸네일 표시
   - 재생 버튼 등
```

## 프론트엔드 사용 예시

### React 예시
```javascript
// 비디오 목록 가져오기
const fetchVideos = async () => {
  const response = await fetch('http://api.matchacake.click/videos/search/');
  const data = await response.json();
  return data.videos;
};

// 사용
const videos = await fetchVideos();
videos.forEach(video => {
  console.log(video.title);        // "인셉션"
  console.log(video.video_url);    // S3 URL
  console.log(video.thumbnail_url); // 썸네일 URL
  console.log(video.duration);     // 8880 (초)
});
```

## 확인 사항

### ✅ 완료된 부분
1. Lambda가 video_assets 저장 (API 호출 없이 직접)
2. Lambda가 contents 저장 (TMDB 정보 사용)
3. FastAPI가 조회 API 제공 (`/videos/search/`, `/videos/watch/{id}`)
4. 조인 쿼리로 contents + video_assets 함께 반환

### ⚠️ 확인 필요
1. FastAPI가 실제로 실행 중인지
2. API 엔드포인트가 프론트엔드에서 접근 가능한지
3. S3 URL이 CloudFront로 변환되는지 (재생용)

## 테스트 방법

### 1. 전체 워크플로우 테스트
```bash
# 1. S3에 업로드
aws s3 cp test_video.mp4 s3://<bucket>/videos/2_test_movie.mp4

# 2. Lambda 로그 확인 (DB 저장 확인)
aws logs tail /aws/lambda/formation-lap-video-processor --follow

# 3. FastAPI로 조회 테스트
curl http://localhost:8000/videos/search/

# 4. 프론트엔드에서 API 호출 테스트
```

### 2. API 응답 확인
```bash
# 비디오 목록
curl http://api.matchacake.click/videos/search/

# 특정 비디오
curl http://api.matchacake.click/videos/watch/1
```

## 결론

**✅ 네, 가능합니다!**

1. ✅ 영상 업로드 → Lambda → DB 저장 완료
2. ✅ FastAPI 조회 API 제공 완료
3. ✅ 프론트엔드가 API로 데이터 가져올 수 있음

**프론트엔드에서 해야 할 일:**
- `GET /videos/search/` 호출
- 응답 JSON 파싱
- 비디오 목록 표시
- 썸네일, 제목, 설명 등 표시
