# Backend/app/common/logger.py
import uuid
import os

def get_request_info():
    """
    고유 Trace ID와 현재 실행 리전 정보를 반환합니다.
    """
    trace_id = str(uuid.uuid4())[:8] # 짧게 8자리만 사용
    region = os.getenv("REGION_NAME", "unknown-region") 
    return trace_id, region
