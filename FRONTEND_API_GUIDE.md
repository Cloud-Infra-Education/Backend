# 프론트엔드 API 사용 가이드

## ✅ 전체 워크플로우

```
1. 사용자가 S3에 영상 업로드
   ↓
2. Lambda 자동 실행 → DB 저장
   - video_assets: video_url, thumbnail_url, duration
   - contents: title, description, age_rating
   ↓
3. 프론트엔드가 FastAPI 호출
   GET /videos/search/
   ↓
4. 웹페이지에 비디오 목록 표시
```

## API 엔드포인트

### 1. 비디오 목록 조회

**엔드포인트:**
```http
GET /videos/search/
GET /videos/search/?q=검색어
```

**응답 예시:**
```json
{
  "query": null,
  "count": 2,
  "videos": [
    {
      "id": 1,
      "title": "인셉션",
      "description": "타인의 꿈에 들어가 생각을 훔치는 특수 보안요원 코브...",
      "age_rating": "12+",
      "like_count": 0,
      "video_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/videos/1_inception.mp4",
      "thumbnail_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/thumbnails/thumb_1_inception.jpg",
      "duration": 8880
    },
    {
      "id": 2,
      "title": "매트릭스",
      "description": "Uploaded video: the_matrix",
      "age_rating": "15+",
      "like_count": 0,
      "video_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/videos/2_the_matrix.mp4",
      "thumbnail_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/thumbnails/thumb_2_the_matrix.jpg",
      "duration": 8160
    }
  ]
}
```

### 2. 비디오 상세 조회

**엔드포인트:**
```http
GET /videos/watch/{video_id}
```

**응답 예시:**
```json
{
  "video": {
    "id": 1,
    "title": "인셉션",
    "description": "타인의 꿈에 들어가 생각을 훔치는 특수 보안요원 코브...",
    "age_rating": "12+",
    "like_count": 0,
    "video_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/videos/1_inception.mp4",
    "thumbnail_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/thumbnails/thumb_1_inception.jpg",
    "duration": 8880
  }
}
```

## 프론트엔드 구현 예시

### React 예시

```javascript
import { useState, useEffect } from 'react';

function VideoList() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await fetch('http://api.matchacake.click/videos/search/');
      const data = await response.json();
      setVideos(data.videos);
      setLoading(false);
    } catch (error) {
      console.error('비디오 목록 가져오기 실패:', error);
      setLoading(false);
    }
  };

  if (loading) return <div>로딩 중...</div>;

  return (
    <div className="video-grid">
      {videos.map(video => (
        <div key={video.id} className="video-card">
          <img 
            src={video.thumbnail_url} 
            alt={video.title}
            className="thumbnail"
          />
          <h3>{video.title}</h3>
          <p>{video.description}</p>
          <div className="meta">
            <span>연령: {video.age_rating}</span>
            <span>길이: {Math.floor(video.duration / 60)}분</span>
            <span>좋아요: {video.like_count}</span>
          </div>
          <video 
            src={video.video_url} 
            controls
            className="video-player"
          />
        </div>
      ))}
    </div>
  );
}

export default VideoList;
```

### 검색 기능

```javascript
const [searchQuery, setSearchQuery] = useState('');

const searchVideos = async (query) => {
  const url = query 
    ? `http://api.matchacake.click/videos/search/?q=${encodeURIComponent(query)}`
    : 'http://api.matchacake.click/videos/search/';
  
  const response = await fetch(url);
  const data = await response.json();
  setVideos(data.videos);
};
```

## 데이터 구조

### Video 객체
```typescript
interface Video {
  id: number;
  title: string;
  description: string;
  age_rating: string;        // "ALL", "12+", "15+", "18+"
  like_count: number;
  video_url: string;          // S3 URL (재생용)
  thumbnail_url: string;      // 썸네일 URL (표시용)
  duration: number;           // 초 단위 (예: 8880 = 148분)
}
```

## 사용 예시

### 1. 비디오 목록 표시
```javascript
// API 호출
const response = await fetch('http://api.matchacake.click/videos/search/');
const data = await response.json();

// 비디오 카드 렌더링
data.videos.forEach(video => {
  console.log(video.title);           // "인셉션"
  console.log(video.thumbnail_url);   // 썸네일 이미지 URL
  console.log(video.video_url);       // 비디오 재생 URL
  console.log(video.duration);        // 8880 (초)
});
```

### 2. 비디오 재생
```html
<video src="{video.video_url}" controls>
  Your browser does not support the video tag.
</video>
```

### 3. 썸네일 표시
```html
<img src="{video.thumbnail_url}" alt="{video.title}" />
```

## 전체 흐름 확인

### Step 1: 영상 업로드
```bash
aws s3 cp video.mp4 s3://bucket/videos/1_inception.mp4
```

### Step 2: Lambda 자동 처리
- ✅ duration 추출
- ✅ 썸네일 생성
- ✅ DB 저장 (video_assets + contents)

### Step 3: 프론트엔드 API 호출
```javascript
fetch('http://api.matchacake.click/videos/search/')
  .then(res => res.json())
  .then(data => {
    // data.videos 배열에 모든 비디오 정보
    // 각 비디오에 video_url, thumbnail_url, duration 포함
  });
```

### Step 4: 웹페이지 표시
- 썸네일 이미지 표시
- 제목, 설명 표시
- 재생 버튼 클릭 시 video_url로 재생

## ✅ 결론

**네, 가능합니다!**

1. ✅ 영상 업로드 → Lambda → DB 저장 완료
2. ✅ FastAPI 조회 API 제공 완료
3. ✅ 썸네일 URL 포함하여 응답
4. ✅ 프론트엔드가 바로 사용 가능

**프론트엔드에서 할 일:**
- `GET /videos/search/` 호출
- 응답 JSON 파싱
- 비디오 카드 렌더링
- 썸네일, 제목, 재생 버튼 표시
