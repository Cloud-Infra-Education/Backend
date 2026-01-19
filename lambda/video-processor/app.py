import os
import json
import boto3
import pymysql
import subprocess
import urllib.parse
import logging
import time
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 클라이언트 설정
s3_config = Config(
    connect_timeout=5,
    read_timeout=10,
    retries={'max_attempts': 1}
)
s3 = boto3.client('s3', config=s3_config)
secrets_client = boto3.client('secretsmanager')

def get_video_info(path):
    """ffprobe를 사용하여 영상의 duration을 추출합니다."""
    try:
        cmd = [
            'ffprobe', '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'json', path
        ]
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=30
        )
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        return int(duration)
    except Exception as e:
        logger.error(f"메타데이터 추출 실패: {str(e)}")
        return 0

def get_db_connection(host, user, password, db_name, max_retries=3, retry_delay=2):
    """RDS Proxy에 연결을 시도합니다. 재시도 로직 포함."""
    for attempt in range(max_retries):
        try:
            logger.info(f"DB 연결 시도 {attempt + 1}/{max_retries}: {host}/{db_name}")
            conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                db=db_name,
                connect_timeout=10,
                read_timeout=30,
                write_timeout=30,
                ssl={'ca': None}  # RDS Proxy는 SSL을 사용하지만 CA 검증은 선택적
            )
            logger.info("DB 연결 성공")
            return conn
        except pymysql.Error as e:
            logger.warning(f"DB 연결 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # 지수 백오프
            else:
                logger.error(f"DB 연결 최종 실패: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"예상치 못한 DB 연결 오류: {str(e)}")
            raise

def get_s3_metadata(bucket, key):
    """S3 객체의 메타데이터와 태그를 가져옵니다."""
    logger.info(f"S3 메타데이터 조회 시작: s3://{bucket}/{key}")
    try:
        # 객체 메타데이터 가져오기
        logger.info("head_object 호출 중...")
        response = s3.head_object(Bucket=bucket, Key=key)
        metadata = response.get('Metadata', {})
        logger.info(f"메타데이터 조회 완료: {len(metadata)} 개")
        
        # 객체 태그 가져오기
        tags = {}
        try:
            logger.info("get_object_tagging 호출 중...")
            tag_response = s3.get_object_tagging(Bucket=bucket, Key=key)
            tags = {tag['Key']: tag['Value'] for tag in tag_response.get('TagSet', [])}
            logger.info(f"태그 조회 완료: {len(tags)} 개")
        except Exception as e:
            logger.warning(f"태그 조회 실패: {str(e)}")
        
        # 메타데이터와 태그 병합 (태그가 우선)
        result = {**metadata, **tags}
        
        metadata_result = {
            'content_id': result.get('content_id') or result.get('ContentId'),
            'title': result.get('title') or result.get('Title') or os.path.splitext(os.path.basename(key))[0],
            'description': result.get('description') or result.get('Description') or '',
            'age_rating': result.get('age_rating') or result.get('AgeRating') or 'ALL',
            'like_count': int(result.get('like_count', 0)) if result.get('like_count') else 0
        }
        logger.info(f"메타데이터 추출 완료: {metadata_result}")
        return metadata_result
    except Exception as e:
        logger.warning(f"S3 메타데이터 조회 실패: {str(e)}. 기본값 사용.")
        filename = os.path.basename(key)
        default_result = {
            'title': os.path.splitext(filename)[0],
            'description': '',
            'age_rating': 'ALL',
            'like_count': 0
        }
        logger.info(f"기본값 반환: {default_result}")
        return default_result

def handler(event, context):
    # 환경 변수 확인 및 로깅
    DB_HOST = os.environ.get('DB_HOST')
    DB_USER = os.environ.get('DB_USER')
    DB_PASS = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    
    logger.info(f"환경 변수 확인 - DB_HOST: {DB_HOST}, DB_USER: {DB_USER}, DB_NAME: {DB_NAME}")
    
    if not all([DB_HOST, DB_USER, DB_PASS, DB_NAME]):
        logger.error("필수 환경 변수가 설정되지 않았습니다!")
        raise ValueError("DB 환경 변수가 누락되었습니다")

    video_local = ""
    thumb_local = ""

    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
        
        filename = os.path.basename(key)
        video_local = f"/tmp/{filename}"
        thumb_name = f"thumb_{filename.rsplit('.', 1)[0]}.jpg"
        thumb_local = f"/tmp/{thumb_name}"

        logger.info(f"영상 처리 시작: {key}")
        logger.info(f"S3 버킷: {bucket}, 키: {key}")
        
        # 파일명에서 content_id 추출 시도 (형식: {content_id}_{timestamp}.mp4)
        content_id_from_filename = None
        try:
            # 파일명 예: "123_20240101120000.mp4" 또는 "videos/123_20240101120000.mp4"
            filename_without_path = os.path.basename(key)
            filename_without_ext = os.path.splitext(filename_without_path)[0]
            # 첫 번째 언더스코어 앞의 숫자를 content_id로 추출
            if '_' in filename_without_ext:
                content_id_from_filename = int(filename_without_ext.split('_')[0])
                logger.info(f"파일명에서 content_id 추출: {content_id_from_filename}")
        except (ValueError, IndexError) as e:
            logger.warning(f"파일명에서 content_id 추출 실패: {str(e)}")
        
        # S3 메타데이터에서 contents 정보 추출
        content_meta = get_s3_metadata(bucket, key)
        logger.info(f"추출된 메타데이터: {content_meta}")
        
        # content_id가 메타데이터에 있으면 사용
        if 'content_id' in content_meta and content_meta['content_id']:
            try:
                content_id_from_meta = int(content_meta['content_id'])
                content_id_from_filename = content_id_from_meta
                logger.info(f"메타데이터에서 content_id 추출: {content_id_from_meta}")
            except (ValueError, TypeError):
                pass
        
        # 영상 다운로드
        logger.info(f"영상 다운로드 시작: s3://{bucket}/{key} -> {video_local}")
        try:
            s3.download_file(bucket, key, video_local)
            file_size = os.path.getsize(video_local)
            logger.info(f"영상 다운로드 완료: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
        except Exception as download_error:
            logger.error(f"영상 다운로드 실패: {str(download_error)}")
            raise

        # 영상 메타데이터 추출 (duration)
        logger.info("FFprobe로 영상 메타데이터 추출 시작")
        video_meta = get_video_info(video_local)
        duration = video_meta if video_meta else 0
        logger.info(f"영상 duration 추출 완료: {duration}초")

        # 썸네일 추출
        logger.info(f"썸네일 추출 시작: {thumb_local}")
        try:
            result = subprocess.run([
                'ffmpeg', '-y', '-i', video_local, 
                '-ss', '00:00:05', '-vframes', '1', thumb_local
            ], check=True, timeout=60, capture_output=True, text=True)
            logger.info(f"썸네일 추출 완료: {os.path.getsize(thumb_local)} bytes")
        except subprocess.TimeoutExpired:
            logger.error("썸네일 추출 타임아웃 (60초 초과)")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"썸네일 추출 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            raise

        thumb_key = f"thumbnails/{thumb_name}"
        s3.upload_file(thumb_local, bucket, thumb_key)

        video_uri = f"s3://{bucket}/{key}"
        thumb_uri = f"s3://{bucket}/{thumb_key}"

        # DB 연결 (재시도 로직 포함)
        conn = get_db_connection(DB_HOST, DB_USER, DB_PASS, DB_NAME)
        
        try:
            with conn.cursor() as cursor:
                # content_id가 파일명이나 메타데이터에서 추출되었다면 해당 content가 존재하는지 확인
                if content_id_from_filename:
                    cursor.execute("SELECT id FROM contents WHERE id = %s", (content_id_from_filename,))
                    existing_content = cursor.fetchone()
                    
                    if existing_content:
                        # 기존 content가 있으면 그대로 사용
                        content_id = content_id_from_filename
                        logger.info(f"기존 content 사용 (content_id: {content_id})")
                    else:
                        # 기존 content가 없으면 새로 생성
                        content_sql = """
                            INSERT INTO contents (title, description, age_rating, like_count)
                            VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(content_sql, (
                            content_meta['title'],
                            content_meta['description'],
                            content_meta['age_rating'],
                            content_meta['like_count']
                        ))
                        content_id = cursor.lastrowid
                        logger.info(f"contents 테이블에 새로 등록 완료 (content_id: {content_id})")
                else:
                    # content_id를 추출할 수 없으면 새로 생성
                    content_sql = """
                        INSERT INTO contents (title, description, age_rating, like_count)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(content_sql, (
                        content_meta['title'],
                        content_meta['description'],
                        content_meta['age_rating'],
                        content_meta['like_count']
                    ))
                    content_id = cursor.lastrowid
                    logger.info(f"contents 테이블에 등록 완료 (content_id: {content_id})")
                
                # 2. video_assets 테이블에 데이터 삽입
                video_sql = """
                    INSERT INTO video_assets 
                    (content_id, video_url, thumbnail_url, duration)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(video_sql, (
                    content_id,
                    video_uri,
                    thumb_uri,
                    duration
                ))
                conn.commit()
                logger.info(f"video_assets 테이블에 등록 완료 (content_id: {content_id})")
        finally:
            conn.close()

        logger.info(f"성공: {key} 등록 완료 (content_id: {content_id})")
        return {
            "status": "success", 
            "content_id": content_id,
            "title": content_meta['title']
        }

    except Exception as e:
        logger.error(f"영상 처리 중 에러 발생: {str(e)}")
        raise e
    finally:
        for f in [video_local, thumb_local]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
