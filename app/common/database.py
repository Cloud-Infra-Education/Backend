# Backend/app/common/database.py
"""
RDS Proxy를 통한 데이터베이스 연결 모듈
환경변수를 통해 현재 리전에 맞는 RDS Proxy 엔드포인트로 연결합니다.
"""

import os
import logging
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from typing import Optional
from contextlib import contextmanager

from .logger import get_request_info, get_region_from_host

# 함수 밖에서 미리 로드합니다.
load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)

# 환경변수 키 정의 (보안 강화를 위해 중앙 관리)
ENV_KEYS = {
    "DB_HOST": "DB_HOST",
    "DB_USER": "DB_USER",
    "DB_PASSWORD": "DB_PASSWORD",
    "DB_NAME": "DB_NAME",
    "DB_PORT": "DB_PORT",
    "REGION_NAME": "REGION_NAME"
}

# RDS Proxy 연결 설정 상수
DEFAULT_DB_PORT = 3306
DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_READ_TIMEOUT = 10
DEFAULT_WRITE_TIMEOUT = 10


def _get_env_var(key: str, required: bool = True) -> Optional[str]:
    """
    환경변수를 안전하게 가져옵니다.
    
    Args:
        key: 환경변수 키
        required: 필수 여부
        
    Returns:
        환경변수 값 또는 None
        
    Raises:
        ValueError: 필수 환경변수가 없을 경우
    """
    value = os.environ.get(key)
    if required and not value:
        raise ValueError(f"[ERROR] 필수 환경 변수가 설정되지 않았습니다: {key}")
    return value


def get_db_connection():
    """
    환경변수를 기반으로 현재 리전의 RDS Proxy에 연결합니다.
    
    Returns:
        pymysql.connections.Connection: 데이터베이스 연결 객체
        
    Raises:
        ValueError: 필수 환경변수가 없을 경우
        pymysql.Error: 데이터베이스 연결 실패 시
    """
    # 환경변수 읽기
    db_host = _get_env_var(ENV_KEYS["DB_HOST"], required=True)
    db_user = _get_env_var(ENV_KEYS["DB_USER"], required=True)
    db_password = _get_env_var(ENV_KEYS["DB_PASSWORD"], required=True)
    db_name = _get_env_var(ENV_KEYS["DB_NAME"], required=True)
    db_port = int(_get_env_var(ENV_KEYS["DB_PORT"], required=False) or DEFAULT_DB_PORT)
    
    # 리전 정보 추출 및 로깅
    region = get_region_from_host(db_host)
    trace_id, region_env = get_request_info()
    
    # 로그 기록 (민감 정보 제외)
    logger.info(
        f"[DB-CONNECTION] 연결 시도 | "
        f"TraceID: {trace_id} | "
        f"Region: {region} | "
        f"Host: {db_host[:20]}... | "
        f"Database: {db_name}"
    )
    
    try:
        # RDS Proxy 연결 시 성능과 안정성을 고려한 설정
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port,
            cursorclass=DictCursor,
            connect_timeout=DEFAULT_CONNECT_TIMEOUT,
            read_timeout=DEFAULT_READ_TIMEOUT,
            write_timeout=DEFAULT_WRITE_TIMEOUT,
            autocommit=True  # RDS Proxy 환경에서 트랜잭션 핀 고정 최소화
        )
        
        logger.info(
            f"[DB-CONNECTION] 연결 성공 | "
            f"TraceID: {trace_id} | "
            f"Region: {region}"
        )
        
        return connection
        
    except pymysql.Error as e:
        logger.error(
            f"[DB-CONNECTION] 연결 실패 | "
            f"TraceID: {trace_id} | "
            f"Region: {region} | "
            f"Error: {str(e)}"
        )
        raise
    except Exception as e:
        logger.error(
            f"[DB-CONNECTION] 예상치 못한 오류 | "
            f"TraceID: {trace_id} | "
            f"Region: {region} | "
            f"Error: {str(e)}"
        )
        raise


@contextmanager
def get_db_cursor():
    """
    데이터베이스 커서를 컨텍스트 매니저로 제공합니다.
    자동으로 연결을 닫아줍니다.
    
    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
    """
    connection = None
    cursor = None
    trace_id, region = get_request_info()
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        logger.debug(f"[DB-CURSOR] 커서 생성 | TraceID: {trace_id} | Region: {region}")
        yield cursor
        connection.commit()
    except Exception as e:
        if connection:
            connection.rollback()
        logger.error(
            f"[DB-CURSOR] 오류 발생 | TraceID: {trace_id} | Region: {region} | Error: {str(e)}"
        )
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            logger.debug(f"[DB-CURSOR] 연결 종료 | TraceID: {trace_id} | Region: {region}")
