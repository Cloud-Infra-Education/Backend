import json
import os
import boto3
import requests
import re
import subprocess
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 환경 변수
CATALOG_API_BASE = os.getenv("CATALOG_API_BASE", "https://api.matchacake.click")
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "formation-lap-internal-token-2024-secret-key")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN", "www.matchacake.click")
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
S3_BUCKET_NAME = os.getenv("S3_BUCKET", "")

s3_client = boto3.client('s3')

def extract_movie_title(filename):
    """파일명에서 검색용 순수 제목 추출 (예: '2_Big_Buck_Bunny.mp4' -> 'Big Buck Bunny')"""
    title = os.path.splitext(filename)[0]
    title = re.sub(r'^\d+[_\-\s]+', '', title)  # 앞의 숫자 제거
    return title.replace("_", " ").replace("-", " ").strip()

def get_video_duration(local_path):
    """FFmpeg Layer를 사용하여 영상 길이 추출"""
    try:
        # Layer 경로(/opt/bin/) 또는 기본 경로 확인
        ffprobe_path = '/opt/bin/ffprobe' if os.path.exists('/opt/bin/ffprobe') else 'ffprobe'
        result = subprocess.run(
            [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', 
             '-of', 'default=noprint_wrappers=1:nokey=1', local_path],
            capture_output=True, text=True, timeout=30
        )
        if result.stdout and result.stdout.strip():
            return int(float(result.stdout.strip()))
        return 0
    except Exception as e:
        logger.error(f"Duration 추출 실패: {e}")
        return 0


def get_tmdb_movie_info(search_title):
    """TMDB API에서 영화 정보 가져오기"""
    if not TMDB_API_KEY:
        return {"title": search_title, "description": "", "age_rating": "ALL", "thumbnail_url": ""}
    
    try:
        # TMDB 검색
        search_res = requests.get(
            f"https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": search_title, "language": "ko-KR"},
            timeout=10
        )
        
        if search_res.status_code != 200 or not search_res.json().get('results'):
            logger.warning(f"TMDB에서 영화를 찾을 수 없습니다: {search_title}")
            return {"title": search_title, "description": "", "age_rating": "ALL", "thumbnail_url": ""}
        
        movie = search_res.json()['results'][0]
        movie_id = movie.get('id')
        
        # 상세 정보 가져오기 (연령 등급 포함)
        detail_res = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY, "language": "ko-KR", "append_to_response": "release_dates"},
            timeout=10
        )
        
        if detail_res.status_code != 200:
            # 검색 결과만 사용
            description = movie.get('overview', '')
            original_title = movie.get('original_title', search_title)
            poster_path = movie.get('poster_path', '')
            thumbnail_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
            return {"title": original_title, "description": description, "age_rating": "ALL", "thumbnail_url": thumbnail_url}
        
        movie_detail = detail_res.json()
        
        # 연령 등급 추출 (한국 기준)
        age_rating = "ALL"
        release_dates = movie_detail.get("release_dates", {}).get("results", [])
        for country in release_dates:
            if country.get("iso_3166_1") == "KR":
                certifications = country.get("release_dates", [])
                if certifications:
                    certification = certifications[0].get("certification", "")
                    if certification:
                        if certification in ["ALL", "12", "15", "18", "R"]:
                            age_rating = certification
                        elif certification == "12세이상관람가":
                            age_rating = "12"
                        elif certification == "15세이상관람가":
                            age_rating = "15"
                        elif certification == "18세이상관람가":
                            age_rating = "18"
                        break
        
        # 정보 추출 (한국어 overview가 비어있으면 영어로 재시도)
        description = movie_detail.get('overview', '') or movie.get('overview', '')
        if not description:
            # 영어로 재시도
            detail_res_en = requests.get(
                f"https://api.themoviedb.org/3/movie/{movie_id}",
                params={"api_key": TMDB_API_KEY, "language": "en-US"},
                timeout=10
            )
            if detail_res_en.status_code == 200:
                movie_detail_en = detail_res_en.json()
                description = movie_detail_en.get('overview', '') or description
        
        original_title = movie_detail.get('original_title', '') or movie.get('original_title', search_title)
        poster_path = movie_detail.get('poster_path', '') or movie.get('poster_path', '')
        thumbnail_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
        
        logger.info(f"✅ TMDB 정보 가져오기 성공: {original_title}")
        return {"title": original_title, "description": description, "age_rating": age_rating, "thumbnail_url": thumbnail_url}
        
    except Exception as e:
        logger.error(f"TMDB API 호출 실패: {e}")
        return {"title": search_title, "description": "", "age_rating": "ALL", "thumbnail_url": ""}

def lambda_handler(event, context):
    """S3 비디오 업로드 시 자동 처리"""
    processed_count = 0
    failed_count = 0
    
    for record in event.get('Records', []):
        try:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            filename = os.path.basename(key)
            
            if not key.endswith('.mp4') or not key.startswith('videos/'):
                logger.info(f"비디오 파일이 아니거나 videos/ 디렉토리가 아닙니다: {key}")
                continue
            
            logger.info(f"========== 비디오 처리 시작: {key} ==========")
            
            # 1. content_id 추출 (파일명에서)
            content_id = int(filename.split('_')[0]) if filename[0].isdigit() else 1
            logger.info(f"추출된 content_id: {content_id}")
            
            # 2. 영화 제목 추출 (TMDB 검색용)
            search_title = extract_movie_title(filename)
            logger.info(f"검색용 제목: {search_title}")
            
            # 3. 비디오 다운로드
            local_video = f"/tmp/{filename}"
            s3_bucket = S3_BUCKET_NAME if S3_BUCKET_NAME else bucket
            logger.info(f"비디오 다운로드 시작: s3://{s3_bucket}/{key}")
            s3_client.download_file(s3_bucket, key, local_video)
            
            # 4. TMDB에서 메타데이터 가져오기
            tmdb_info = get_tmdb_movie_info(search_title)
            final_title = tmdb_info.get("title", search_title)
            description = tmdb_info.get("description", "")
            age_rating = tmdb_info.get("age_rating", "ALL")
            tmdb_thumb = tmdb_info.get("thumbnail_url", "")
            
            # 5. 비디오 정보 추출
            duration = get_video_duration(local_video)
            logger.info(f"Duration: {duration}초")
            
            video_url = f"https://{CLOUDFRONT_DOMAIN}/{key}"
            
            # 6. 썸네일 URL (TMDB poster_path 사용)
            final_thumb = tmdb_thumb
            if not final_thumb:
                logger.warning("TMDB 썸네일을 가져올 수 없습니다. 썸네일 없이 진행합니다.")
            
            # 7. API를 통한 데이터 저장
            headers = {"Content-Type": "application/json", "X-Internal-Token": INTERNAL_TOKEN}
            base_url = CATALOG_API_BASE.rstrip('/')
            if not base_url.endswith('/api'):
                base_url = f"{base_url}/api"
            
            # 7-1. Contents 저장 (메타데이터)
            logger.info(f"Contents 생성 시작: title={final_title}")
            content_res = requests.post(
                f"{base_url}/v1/contents",
                headers=headers,
                json={
                    "title": final_title,
                    "description": description,
                    "age_rating": age_rating
                },
                timeout=10
            )
            
            if content_res.status_code not in [200, 201]:
                logger.error(f"Contents 생성 실패: {content_res.status_code} - {content_res.text}")
                failed_count += 1
                continue
            
            content_data = content_res.json()
            actual_content_id = content_data.get('id', content_id)
            logger.info(f"✅ Contents 생성 완료: ID={actual_content_id}, title={final_title}")
            
            # 7-2. Video Assets 저장 (video_url, thumbnail_url, duration)
            logger.info(f"Video Assets 생성 시작: content_id={actual_content_id}")
            asset_res = requests.post(
                f"{base_url}/v1/contents/{actual_content_id}/video-assets",
                headers=headers,
                json={
                    "content_id": actual_content_id,
                    "video_url": video_url,
                    "thumbnail_url": final_thumb if final_thumb else None,
                    "duration": duration if duration > 0 else None
                },
                timeout=10
            )
            
            if asset_res.status_code not in [200, 201]:
                logger.error(f"Video Assets 생성 실패: {asset_res.status_code} - {asset_res.text}")
                failed_count += 1
                continue
            
            logger.info(f"✅ Video Assets 생성 완료: content_id={actual_content_id}")
            processed_count += 1
            
            # 임시 파일 정리
            if os.path.exists(local_video):
                os.remove(local_video)
            
        except Exception as e:
            logger.error(f"비디오 처리 중 오류 발생: {e}", exc_info=True)
            failed_count += 1
            continue
    
    logger.info(f"Lambda 함수 완료: 처리={processed_count}, 실패={failed_count}, 전체={processed_count + failed_count}")
    return {"statusCode": 200, "body": json.dumps({"processed": processed_count, "failed": failed_count})}
