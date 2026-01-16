# Video Processing API 구현 문서

## 개요
S3에 업로드된 영상 파일을 처리하여 메타데이터를 추출하고 Backend API에 저장하는 Lambda 함수 및 관련 API 엔드포인트를 구현했습니다.

## 구현 내용

### 1. Lambda 함수 (`lambda/video-processor/app.py`)

#### 1.1 주요 기능
1. **S3 이벤트 처리**: S3에 영상 파일 업로드 시 자동 트리거
2. **영화 제목 추출**: 파일명에서 숫자 prefix 제거 (예: `2_Big_Buck_Bunny.mp4` → `Big Buck Bunny`)
3. **TMDB API 통합**: 영화 메타데이터 조회 (제목, 설명, 연령 등급, 포스터)
4. **비디오 메타데이터 추출**: FFprobe를 사용한 duration 추출
5. **Backend API 연동**: Contents 및 Video Assets 생성

#### 1.2 처리 플로우
```
S3 영상 업로드
  ↓
Lambda 함수 트리거
  ↓
파일명에서 content_id 및 영화 제목 추출
  ↓
S3에서 비디오 다운로드
  ↓
TMDB API에서 영화 정보 조회
  ↓
FFprobe로 duration 추출
  ↓
Contents API로 메타데이터 저장
  ↓
Video Assets API로 video_url, thumbnail_url, duration 저장
```

#### 1.3 주요 함수

##### `extract_movie_title(filename)`
- 파일명에서 영화 제목 추출
- 숫자 prefix 제거 (예: `2_Big_Buck_Bunny.mp4` → `Big Buck Bunny`)
- 언더스코어를 공백으로 변환

##### `get_tmdb_movie_info(search_title)`
- TMDB API를 통한 영화 정보 조회
- 검색 → 상세 정보 조회 → 연령 등급 추출
- 한국어 실패 시 영어로 재시도
- 반환: `{title, description, age_rating, thumbnail_url}`

##### `get_video_duration(video_path)`
- FFprobe를 사용한 비디오 duration 추출
- FFmpeg Layer의 `/opt/bin/ffprobe` 사용
- 실패 시 0 반환

##### `lambda_handler(event, context)`
- S3 이벤트 처리 메인 함수
- 여러 파일 동시 처리 지원
- 에러 처리 및 로깅

### 2. API 엔드포인트

#### 2.1 Contents API (`app/api/v1/routes/contents.py`)
- **POST** `/api/v1/contents`: 컨텐츠 생성
- **GET** `/api/v1/contents`: 컨텐츠 목록 조회
- **GET** `/api/v1/contents/{content_id}`: 컨텐츠 상세 조회
- **PUT** `/api/v1/contents/{content_id}`: 컨텐츠 수정
- **DELETE** `/api/v1/contents/{content_id}`: 컨텐츠 삭제

#### 2.2 Video Assets API (`app/api/v1/routes/video_assets.py`)
- **POST** `/api/v1/contents/{content_id}/video-assets`: 영상 파일 정보 생성
- **GET** `/api/v1/contents/{content_id}/video-assets`: 영상 파일 정보 목록 조회
- **GET** `/api/v1/contents/{content_id}/video-assets/{asset_id}`: 영상 파일 정보 상세 조회
- **PUT** `/api/v1/contents/{content_id}/video-assets/{asset_id}`: 영상 파일 정보 수정
- **DELETE** `/api/v1/contents/{content_id}/video-assets/{asset_id}`: 영상 파일 정보 삭제
- **GET** `/api/v1/contents/{content_id}/video-assets/s3/list`: S3 버킷에서 영상 파일 목록 조회
- **GET** `/api/v1/contents/{content_id}/video-assets/s3/url/{s3_key}`: S3 파일의 CloudFront URL 조회

### 3. 데이터 모델

#### 3.1 Content 모델 (`app/models/content.py`)
```python
- id: Integer (Primary Key)
- title: String (영화 제목)
- description: String (영화 설명)
- age_rating: String (연령 등급: ALL, 12, 15, 18, R)
- like_count: Integer (좋아요 수)
- created_at: DateTime
- updated_at: DateTime
```

#### 3.2 VideoAsset 모델 (`app/models/video_asset.py`)
```python
- id: Integer (Primary Key)
- content_id: Integer (Foreign Key → contents.id)
- video_url: String (CloudFront URL)
- thumbnail_url: String (TMDB 포스터 URL)
- duration: Float (영상 길이, 초 단위)
- created_at: DateTime
```

### 4. 스키마 정의

#### 4.1 VideoAsset 스키마 (`app/schemas/video_asset.py`)
- `VideoAssetBase`: 기본 스키마
- `VideoAssetCreate`: 생성용 스키마
- `VideoAssetUpdate`: 수정용 스키마
- `VideoAssetResponse`: 응답용 스키마

### 5. S3 서비스 (`app/services/s3_service.py`)

#### 5.1 주요 메서드
- `list_videos(prefix, max_keys)`: S3 버킷에서 영상 파일 목록 조회
- `get_file_info(s3_key)`: 특정 S3 파일 정보 조회
- `get_cloudfront_url(s3_key)`: S3 키를 CloudFront URL로 변환

### 6. 사용 기술

- **Python 3.11**: Lambda 함수 런타임
- **FastAPI**: Backend API 프레임워크
- **SQLAlchemy**: ORM
- **Pydantic**: 데이터 검증
- **boto3**: AWS SDK (S3 접근)
- **requests**: HTTP 클라이언트 (TMDB API, Backend API 호출)
- **FFmpeg/FFprobe**: 비디오 메타데이터 추출
- **TMDB API**: 영화 메타데이터 조회

### 7. 환경 변수

Lambda 함수에서 사용하는 환경 변수:
- `CATALOG_API_BASE`: Backend API 기본 URL
- `INTERNAL_TOKEN`: 내부 API 인증 토큰
- `S3_BUCKET`: S3 버킷 이름
- `S3_REGION`: S3 리전
- `CLOUDFRONT_DOMAIN`: CloudFront 도메인
- `TMDB_API_KEY`: TMDB API 키
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`: 데이터베이스 연결 정보

### 8. 주요 파일

- `lambda/video-processor/app.py`: Lambda 함수 메인 코드
- `lambda/video-processor/requirements.txt`: Python 의존성
- `app/api/v1/routes/video_assets.py`: Video Assets API 엔드포인트
- `app/api/v1/routes/contents.py`: Contents API 엔드포인트
- `app/models/video_asset.py`: VideoAsset 모델
- `app/schemas/video_asset.py`: VideoAsset 스키마
- `app/services/s3_service.py`: S3 서비스

### 9. 데이터 흐름

```
1. 사용자가 S3에 영상 업로드
   ↓
2. S3 이벤트 트리거 → Lambda 함수 실행
   ↓
3. Lambda 함수:
   - 파일명에서 영화 제목 추출
   - S3에서 비디오 다운로드
   - TMDB API에서 영화 정보 조회
   - FFprobe로 duration 추출
   ↓
4. Backend API 호출:
   - POST /api/v1/contents (메타데이터 저장)
   - POST /api/v1/contents/{content_id}/video-assets (비디오 정보 저장)
   ↓
5. 프론트엔드에서 API 조회:
   - GET /api/v1/contents (목록)
   - GET /api/v1/contents/{content_id}/video-assets (비디오 정보)
```

### 10. 트러블슈팅

#### 10.1 TMDB API 언어 문제
- **문제**: 한국어로 요청 시 `overview`가 비어있음
- **해결**: 한국어 실패 시 영어로 재시도하는 로직 추가

#### 10.2 파일명에서 제목 추출
- **문제**: `2_Big_Buck_Bunny.mp4` 같은 파일명 처리
- **해결**: 숫자 prefix 제거 및 언더스코어를 공백으로 변환

#### 10.3 FFprobe 경로 문제
- **문제**: Lambda 환경에서 FFprobe 경로 찾기 실패
- **해결**: FFmpeg Layer의 `/opt/bin/ffprobe` 경로 사용
