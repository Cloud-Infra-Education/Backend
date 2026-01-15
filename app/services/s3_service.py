"""
S3 Service
S3 파일 목록 조회 및 CloudFront URL 생성
"""
import boto3
from typing import List, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """S3 서비스 클래스"""
    
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.S3_REGION
        self.cloudfront_domain = settings.CLOUDFRONT_DOMAIN
        
        # S3 클라이언트 초기화 (IRSA 또는 환경 변수에서 자동으로 자격 증명 가져옴)
        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
        except Exception as e:
            logger.warning(f"S3 클라이언트 초기화 실패: {e}")
            self.s3_client = None
    
    def is_available(self) -> bool:
        """S3 서비스 사용 가능 여부 확인"""
        return self.s3_client is not None and self.bucket_name is not None
    
    def list_videos(self, prefix: Optional[str] = None, max_keys: int = 1000) -> List[dict]:
        """
        S3 버킷에서 영상 파일 목록 조회
        
        Args:
            prefix: 파일 경로 prefix (예: "videos/", "content/1/")
            max_keys: 최대 반환 개수
            
        Returns:
            파일 정보 리스트 [{"key": "path/to/video.mp4", "size": 12345, "url": "https://..."}, ...]
        """
        if not self.is_available():
            logger.warning("S3 서비스가 사용 불가능합니다.")
            return []
        
        try:
            # S3 객체 목록 조회
            params = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }
            
            if prefix:
                params['Prefix'] = prefix
            
            response = self.s3_client.list_objects_v2(**params)
            
            if 'Contents' not in response:
                return []
            
            # 영상 파일 확장자 필터링
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v', '.flv'}
            
            files = []
            for obj in response['Contents']:
                key = obj['Key']
                # 디렉토리는 제외
                if key.endswith('/'):
                    continue
                
                # 영상 파일만 필터링
                if any(key.lower().endswith(ext) for ext in video_extensions):
                    file_info = {
                        'key': key,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'url': self.get_cloudfront_url(key)
                    }
                    files.append(file_info)
            
            return files
            
        except ClientError as e:
            logger.error(f"S3 파일 목록 조회 실패: {e}")
            return []
        except NoCredentialsError:
            logger.error("AWS 자격 증명을 찾을 수 없습니다.")
            return []
        except Exception as e:
            logger.error(f"S3 서비스 오류: {e}")
            return []
    
    def get_cloudfront_url(self, s3_key: str) -> str:
        """
        S3 키를 CloudFront URL로 변환
        
        Args:
            s3_key: S3 객체 키 (예: "videos/content1.mp4")
            
        Returns:
            CloudFront URL (예: "https://www.exampleott.click/videos/content1.mp4")
        """
        if self.cloudfront_domain:
            # CloudFront 도메인이 설정된 경우
            return f"https://{self.cloudfront_domain}/{s3_key}"
        else:
            # CloudFront 도메인이 없는 경우 S3 URL 반환
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
    
    def get_file_info(self, s3_key: str) -> Optional[dict]:
        """
        특정 S3 파일 정보 조회
        
        Args:
            s3_key: S3 객체 키
            
        Returns:
            파일 정보 또는 None
        """
        if not self.is_available():
            return None
        
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'key': s3_key,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType', ''),
                'last_modified': response['LastModified'].isoformat(),
                'url': self.get_cloudfront_url(s3_key)
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"S3 파일을 찾을 수 없습니다: {s3_key}")
            else:
                logger.error(f"S3 파일 정보 조회 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"S3 서비스 오류: {e}")
            return None


# 싱글톤 인스턴스
s3_service = S3Service()
