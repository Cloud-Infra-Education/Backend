# Backend/app/common/logger.py
import uuid
import os
import logging
from typing import Tuple

# 로거 설정
logger = logging.getLogger(__name__)

# 리전 매핑 설정 (환경변수로 관리 가능하도록)
REGION_MAPPING = {
    "ap-northeast-2": "seoul",
    "us-west-2": "oregon",
    "seoul": "seoul",
    "oregon": "oregon"
}

def get_request_info() -> Tuple[str, str]:
    """
    고유 Trace ID와 현재 실행 리전 정보를 반환합니다.
    
    Returns:
        Tuple[str, str]: (trace_id, region_name) 형태의 튜플
    """
    trace_id = str(uuid.uuid4())[:8]  # 짧게 8자리만 사용
    region_env = os.getenv("REGION_NAME", "unknown-region")
    
    # 환경변수에서 리전 정보를 정규화
    region = REGION_MAPPING.get(region_env.lower(), region_env.lower())
    
    return trace_id, region

def get_region_from_host(host: str) -> str:
    """
    RDS Proxy 엔드포인트에서 리전 정보를 추출합니다.
    
    Args:
        host: RDS Proxy 엔드포인트 주소
        
    Returns:
        str: 리전 이름 (seoul, oregon 등)
    """
    if not host:
        return "unknown"
    
    host_lower = host.lower()
    for aws_region, region_name in REGION_MAPPING.items():
        if aws_region in host_lower:
            return region_name
    
    return "unknown"
