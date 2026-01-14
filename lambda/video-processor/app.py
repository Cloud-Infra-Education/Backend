import os
import json
import boto3
import pymysql
import subprocess
import urllib.parse
import logging
import time
import requests
from botocore.config import Config

# Paramiko DSSKey 호환성 패치 (sshtunnel import 전에 실행)
# Lambda 기본 런타임의 paramiko와 sshtunnel 버전 차이 해결
try:
    import paramiko
    if not hasattr(paramiko, "DSSKey"):
        # DSA 키는 사용하지 않으므로, 존재 여부만 맞춰주기 위한 더미 클래스
        class _DummyDSSKey:
            pass
        paramiko.DSSKey = _DummyDSSKey  # type: ignore[attr-defined]
        # sys.modules에도 반영하여 sshtunnel이 같은 paramiko를 사용하도록
        import sys
        sys.modules['paramiko'].DSSKey = _DummyDSSKey  # type: ignore[attr-defined]
except Exception as e:
    logging.warning(f"Paramiko DSSKey 패치 실패: {e}")

from sshtunnel import SSHTunnelForwarder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# FFmpeg / FFprobe 실행 경로 (Lambda 컨테이너 이미지에 설치된 위치)
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", "/usr/local/bin/ffmpeg")
FFPROBE_PATH = os.environ.get("FFPROBE_PATH", "/usr/local/bin/ffprobe")

# S3 클라이언트 설정
s3_config = Config(
    connect_timeout=5,
    read_timeout=10,
    retries={'max_attempts': 1}
)
s3 = boto3.client('s3', config=s3_config)
secrets_client = boto3.client('secretsmanager')
secrets_manager = boto3.client('secretsmanager')

def get_video_info(path):
    """ffprobe를 사용하여 영상의 duration을 추출합니다."""
    try:
        cmd = [
            FFPROBE_PATH, '-v', 'error',
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

def get_db_connection(host, user, password, db_name, bastion_host=None, bastion_user="ec2-user", bastion_key_path=None, rds_endpoint=None, rds_port=3306, max_retries=3, retry_delay=2):
    """
    RDS Proxy에 연결을 시도합니다. 재시도 로직 포함.
    Bastion을 통한 SSH 터널링을 지원합니다.
    """
    tunnel = None
    
    try:
        # Bastion을 통한 연결인 경우 SSH 터널 생성
        if bastion_host and rds_endpoint:
            logger.info(f"SSH 터널링을 통한 연결: Bastion({bastion_host}) -> RDS({rds_endpoint}:{rds_port})")

            # SSH 키 경로 확인 (Lambda 환경에서는 /tmp에 저장된 키 사용)
            if not bastion_key_path or not os.path.exists(bastion_key_path):
                # 이 시점에 도달했다는 것은 handler에서 Secrets Manager 설정이 잘못되었다는 의미
                msg = (
                    "Bastion SSH 키 파일이 존재하지 않습니다. "
                    "Secrets Manager에 SSH 개인키가 제대로 저장되었는지 확인하세요."
                )
                logger.error(msg)
                raise ValueError(msg)

            ssh_key = bastion_key_path

            # SSH 터널 생성 (로컬 포트는 자동 할당)
            tunnel = SSHTunnelForwarder(
                (bastion_host, 22),
                ssh_username=bastion_user,
                ssh_pkey=ssh_key,
                remote_bind_address=(rds_endpoint, rds_port),
                local_bind_address=('127.0.0.1', 0)  # 0은 자동 포트 할당
            )
            tunnel.start()
            local_port = tunnel.local_bind_port
            logger.info(f"SSH 터널 생성 완료: localhost:{local_port} -> {rds_endpoint}:{rds_port}")
            actual_host = '127.0.0.1'
            actual_port = local_port
        else:
            # 직접 연결
            actual_host = host
            actual_port = rds_port
        
        # DB 연결 시도
        for attempt in range(max_retries):
            try:
                logger.info(f"DB 연결 시도 {attempt + 1}/{max_retries}: {actual_host}:{actual_port}/{db_name}")
                conn = pymysql.connect(
                    host=actual_host,
                    port=actual_port,
                    user=user,
                    password=password,
                    db=db_name,
                    connect_timeout=10,
                    read_timeout=30,
                    write_timeout=30,
                    ssl={'ca': None}  # RDS Proxy는 SSL을 사용하지만 CA 검증은 선택적
                )
                logger.info("DB 연결 성공")
                # 연결 객체에 터널 참조 저장 (나중에 닫기 위해)
                if tunnel:
                    conn._tunnel = tunnel
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
    except Exception as e:
        if tunnel:
            tunnel.stop()
        raise

def slug_to_title(slug: str) -> str:
    """slug를 사람이 읽을 수 있는 title로 변환"""
    slug = slug.replace("-", " ").replace("_", " ").strip()
    return " ".join([w.capitalize() for w in slug.split()]) if slug else "Untitled"


def extract_slug_from_filename(key: str) -> str:
    """파일명에서 slug 추출 (예: videos/1_test_video.mp4 -> test_video)"""
    filename = os.path.basename(key)
    name_no_ext = os.path.splitext(filename)[0]  # 1_test_video
    parts = name_no_ext.split("_", 1)
    if len(parts) > 1:
        return parts[1]  # test_video
    return name_no_ext  # fallback


def get_tmdb_info(search_query: str):
    """
    TMDB API를 사용하여 영상 정보 가져오기
    Returns: (title, description, age_rating) 또는 None
    """
    tmdb_api_key = os.environ.get("TMDB_API_KEY", "")
    if not tmdb_api_key:
        logger.warning("TMDB_API_KEY가 설정되지 않아 TMDB 정보를 가져올 수 없습니다.")
        return None
    
    try:
        # TMDB 검색 API
        search_url = f"https://api.themoviedb.org/3/search/movie"
        search_params = {
            "api_key": tmdb_api_key,
            "query": search_query,
            "language": "ko-KR"
        }
        
        logger.info(f"TMDB 검색 시작: {search_query}")
        search_response = requests.get(search_url, params=search_params, timeout=5)
        
        if search_response.status_code != 200:
            logger.warning(f"TMDB 검색 실패: {search_response.status_code}")
            return None
        
        search_data = search_response.json()
        results = search_data.get("results", [])
        
        if not results:
            logger.warning(f"TMDB 검색 결과 없음: {search_query}")
            return None
        
        # 첫 번째 결과 사용
        movie = results[0]
        movie_id = movie.get("id")
        
        if not movie_id:
            return None
        
        # 영화 상세 정보 가져오기
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        detail_params = {
            "api_key": tmdb_api_key,
            "language": "ko-KR",
            "append_to_response": "release_dates"
        }
        
        detail_response = requests.get(detail_url, params=detail_params, timeout=5)
        
        if detail_response.status_code != 200:
            logger.warning(f"TMDB 상세 정보 조회 실패: {detail_response.status_code}")
            # 검색 결과만 사용
            title = movie.get("title", "")
            description = movie.get("overview", "")
            age_rating = "ALL"  # 기본값
            
            return {
                "title": title,
                "description": description or f"Uploaded video: {search_query}",
                "age_rating": age_rating
            }
        
        detail_data = detail_response.json()
        
        # 제목과 설명
        title = detail_data.get("title", movie.get("title", ""))
        description = detail_data.get("overview", movie.get("overview", ""))
        
        # 연령 등급 (certification) 가져오기 - 한국(KR)만 사용
        age_rating = "ALL"  # 기본값
        release_dates = detail_data.get("release_dates", {})
        results_list = release_dates.get("results", [])
        
        # 한국(KR) 등급만 찾기
        for country_data in results_list:
            country_code = country_data.get("iso_3166_1", "")
            
            # 한국 등급만 사용
            if country_code == "KR":
                release_dates_list = country_data.get("release_dates", [])
                
                for release in release_dates_list:
                    certification = release.get("certification", "")
                    if certification:
                        # 한국 등급 변환: 12, 15, 18 → 12+, 15+, 18+
                        if certification in ["12", "15", "18"]:
                            age_rating = f"{certification}+"
                        else:
                            age_rating = "ALL"
                        break
                
                # 한국 등급을 찾았으면 더 이상 검색하지 않음
                if age_rating != "ALL":
                    break
        
        logger.info(f"TMDB 정보 가져오기 성공: {title}, age_rating: {age_rating}")
        
        return {
            "title": title,
            "description": description or f"Uploaded video: {search_query}",
            "age_rating": age_rating
        }
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"TMDB API 호출 실패: {str(e)}")
        return None
    except Exception as e:
        logger.warning(f"TMDB 정보 처리 실패: {str(e)}")
        return None


def upsert_contents_via_api(content_id: int, key: str):
    """
    FastAPI의 내부 upsert 엔드포인트를 호출하여 contents를 채움
    TMDB API를 사용하여 영상 정보를 가져옴
    """
    api_base = os.environ.get("CATALOG_API_BASE", "").rstrip("/")
    token = os.environ.get("INTERNAL_TOKEN", "")
    
    if not api_base or not token:
        logger.warning("CATALOG_API_BASE 또는 INTERNAL_TOKEN이 설정되지 않아 API 호출을 건너뜁니다.")
        return
    
    try:
        slug = extract_slug_from_filename(key)
        
        # TMDB API로 영상 정보 가져오기
        tmdb_info = get_tmdb_info(slug)
        
        if tmdb_info:
            # TMDB에서 가져온 정보 사용
            title = tmdb_info["title"]
            description = tmdb_info["description"]
            age_rating = tmdb_info["age_rating"]
            logger.info(f"TMDB 정보 사용: {title}, age_rating: {age_rating}")
        else:
            # TMDB 실패 시 파일명에서 추출
            title = slug_to_title(slug)
            description = f"Uploaded video: {slug}"
            age_rating = "ALL"
            logger.info(f"TMDB 정보 없음, 파일명에서 추출: {title}")
        
        payload = {
            "title": title,
            "description": description,
            "age_rating": age_rating
        }
        
        url = f"{api_base}/v1/contents/{content_id}/upsert-internal"
        logger.info(f"FastAPI upsert 호출 시작: {url}")
        
        r = requests.put(
            url,
            json=payload,
            headers={"X-Internal-Token": token},
            timeout=10
        )
        
        if r.status_code >= 300:
            raise RuntimeError(f"contents upsert failed: {r.status_code} {r.text}")
        
        logger.info(f"FastAPI upsert 성공: content_id={content_id}, title={title}")
    except requests.exceptions.RequestException as e:
        logger.error(f"FastAPI 호출 중 네트워크 오류: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"FastAPI upsert 실패: {str(e)}")
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
    BASTION_HOST = os.environ.get('BASTION_HOST')  # Bastion Private IP
    BASTION_USER = os.environ.get('BASTION_USER', 'ec2-user')
    BASTION_SSH_KEY_SECRET = os.environ.get('BASTION_SSH_KEY_SECRET')  # Secrets Manager Secret 이름
    PROXY_ENDPOINT = os.environ.get('PROXY_ENDPOINT')  # RDS Proxy Endpoint
    DB_HOST = os.environ.get('DB_HOST')  # 직접 연결 시 사용
    DB_USER = os.environ.get('DB_USER')
    DB_PASS = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    RDS_PORT = int(os.environ.get('RDS_PORT', '3306'))
    
    # Secrets Manager에서 DB credentials 가져오기 (formation-lap/db/dev/credentials에서)
    bastion_ssh_key_path = None
    DB_CREDENTIALS_SECRET = os.environ.get('DB_CREDENTIALS_SECRET', 'formation-lap/db/dev/credentials')
    
    # Bastion을 통한 SSH 터널링 연결인지 확인
    # 주의: 현재 네트워크 설정상 Lambda는 VPC 내부에서 RDS Proxy로 직접 접속 가능
    # 따라서 Bastion SSH 터널링은 우회하고 직접 연결 사용
    use_bastion = False  # 임시로 비활성화 (Bastion 접속 문제로 인해)
    
    # Bastion을 사용하는 경우에만 SSH 키 가져오기
    if use_bastion:
        try:
            logger.info(f"Secrets Manager에서 DB credentials 및 SSH 키 가져오기: {DB_CREDENTIALS_SECRET}")
            secret_response = secrets_manager.get_secret_value(SecretId=DB_CREDENTIALS_SECRET)
            secret_data = json.loads(secret_response['SecretString'])

            # 어떤 필드 이름으로 SSH 키가 들어있는지 모를 수 있으므로, 여러 후보 키를 순서대로 탐색
            ssh_key_field_candidates = [
                "ssh_key",
                "bastion_ssh_key",
                "bastion_private_key",
                "bastion_ssh_private_key",
                "private_key",
            ]
            ssh_key_content = None

            logger.info(f"Secrets Manager JSON 키 목록: {list(secret_data.keys())}")

            for field in ssh_key_field_candidates:
                if field in secret_data and secret_data[field]:
                    ssh_key_content = secret_data[field]
                    logger.info(f"SSH 키 필드 사용: {field}")
                    break

            if ssh_key_content:
                # /tmp에 키 파일 저장
                bastion_ssh_key_path = "/tmp/bastion_ssh_key.pem"
                with open(bastion_ssh_key_path, "w") as f:
                    f.write(ssh_key_content)
                os.chmod(bastion_ssh_key_path, 0o400)  # 읽기 전용
                logger.info(f"SSH 키 저장 완료: {bastion_ssh_key_path}")
            else:
                # SSH 키가 전혀 없는 경우에는 IAM 역할 기반 인증으로는 Bastion에 접속할 수 없으므로,
                # 조용히 넘어가지 말고 명시적으로 에러를 발생시켜 Secret 구성을 수정하도록 유도
                msg = (
                    "Secrets Manager에 SSH 개인키가 없습니다. "
                    "다음 필드 중 하나로 SSH 개인키를 추가해야 합니다: "
                    f"{ssh_key_field_candidates}"
                )
                logger.error(msg)
                raise ValueError(msg)
        except Exception as e:
            logger.error(f"Secrets Manager에서 SSH 키 가져오기 실패: {str(e)}")
            # 여기서 바로 예외를 던져서, SSH 키 없이 Bastion에 접속을 시도하지 않도록 한다.
            raise
    else:
        logger.info("Bastion 우회 모드: SSH 키 불필요")
    
    if use_bastion:
        logger.info(f"SSH 터널링 모드 - BASTION_HOST: {BASTION_HOST}, PROXY_ENDPOINT: {PROXY_ENDPOINT}")
    else:
        logger.info(f"직접 연결 모드 - DB_HOST: {DB_HOST or PROXY_ENDPOINT}")
    
    logger.info(f"환경 변수 확인 - DB_USER: {DB_USER}, DB_NAME: {DB_NAME}")
    
    if not all([DB_USER, DB_PASS, DB_NAME]):
        logger.error("필수 환경 변수가 설정되지 않았습니다!")
        raise ValueError("DB 환경 변수가 누락되었습니다")
    
    if use_bastion and not PROXY_ENDPOINT:
        logger.error("Bastion 모드인데 PROXY_ENDPOINT가 설정되지 않았습니다!")
        raise ValueError("PROXY_ENDPOINT 환경 변수가 누락되었습니다")

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
                FFMPEG_PATH, '-y', '-i', video_local,
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
        # Lambda는 VPC 내부에서 RDS Proxy로 직접 접속 가능 (SG 규칙 있음)
        # Bastion SSH 터널링은 네트워크 문제로 인해 우회
        proxy_host = PROXY_ENDPOINT or DB_HOST
        logger.info(f"RDS Proxy 직접 연결 시도: {proxy_host}:{RDS_PORT}/{DB_NAME}")
        conn = get_db_connection(
            host=proxy_host,
            user=DB_USER,
            password=DB_PASS,
            db_name=DB_NAME,
            bastion_host=None,  # Bastion 우회
            rds_port=RDS_PORT
        )
        
        try:
            with conn.cursor() as cursor:
                # content_id가 파일명이나 메타데이터에서 추출되었는지 확인
                if content_id_from_filename:
                    content_id = content_id_from_filename
                    logger.info(f"파일명에서 content_id 추출: {content_id}")
                else:
                    # content_id를 추출할 수 없으면 새로 생성 (임시 ID)
                    # 주의: AUTO_INCREMENT이므로 INSERT 후 lastrowid 사용
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
                    conn.commit()
                    logger.info(f"contents 테이블에 새로 등록 완료 (content_id: {content_id})")
                
                # FastAPI 내부 upsert API 호출하여 contents 채우기
                # 파일명에서 slug 추출하여 title 생성
                try:
                    upsert_contents_via_api(content_id, key)
                    logger.info(f"FastAPI upsert 성공: content_id={content_id}")
                except Exception as api_error:
                    logger.warning(f"FastAPI upsert 호출 실패, DB에 직접 저장: {str(api_error)}")
                    # API 호출 실패 시 Lambda에서 직접 contents 테이블에 저장
                    slug = extract_slug_from_filename(key)
                    
                    # TMDB API로 영상 정보 가져오기
                    tmdb_info = get_tmdb_info(slug)
                    
                    if tmdb_info:
                        # TMDB에서 가져온 정보 사용
                        title = tmdb_info["title"]
                        description = tmdb_info["description"]
                        age_rating = tmdb_info["age_rating"]
                        logger.info(f"TMDB 정보 사용 (DB 직접 저장): {title}, age_rating: {age_rating}")
                    else:
                        # TMDB 실패 시 파일명에서 추출
                        title = slug_to_title(slug)
                        description = f"Uploaded video: {slug}"
                        age_rating = "ALL"
                        logger.info(f"TMDB 정보 없음, 파일명에서 추출 (DB 직접 저장): {title}")
                    
                    # contents 테이블에 저장 (upsert)
                    content_check_sql = "SELECT id FROM contents WHERE id = %s"
                    cursor.execute(content_check_sql, (content_id,))
                    existing_content = cursor.fetchone()
                    
                    if existing_content:
                        # 기존 content 업데이트
                        content_update_sql = """
                            UPDATE contents 
                            SET title = %s, description = %s, age_rating = %s
                            WHERE id = %s
                        """
                        cursor.execute(content_update_sql, (title, description, age_rating, content_id))
                    else:
                        # 새 content 생성
                        content_insert_sql = """
                            INSERT INTO contents (id, title, description, age_rating, like_count)
                            VALUES (%s, %s, %s, %s, 0)
                        """
                        cursor.execute(content_insert_sql, (content_id, title, description, age_rating))
                    
                    conn.commit()
                    logger.info(f"contents 테이블에 직접 저장 완료 (content_id: {content_id}, title: {title})")
                
                # video_assets 테이블에 데이터 삽입
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
            # SSH 터널이 있으면 먼저 닫기
            if hasattr(conn, '_tunnel') and conn._tunnel:
                try:
                    conn._tunnel.stop()
                    logger.info("SSH 터널 종료 완료")
                except:
                    pass
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
        # 임시 파일 정리
        for f in [video_local, thumb_local]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        
        # SSH 키 파일 정리
        if bastion_ssh_key_path and os.path.exists(bastion_ssh_key_path):
            try:
                os.remove(bastion_ssh_key_path)
                logger.info("SSH 키 파일 정리 완료")
            except:
                pass