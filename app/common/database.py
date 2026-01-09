# Backend/app/common/database.py
import os
import pymysql
from pymysql.cursors import DictCursor

def get_db_connection():
    """
    환경 변수를 읽어 현재 리전의 RDS Proxy에 접속하는 커넥션 객체를 반환합니다.
    """
    # EKS 배포 시 테라폼의 rds_proxy_endpoint_xxxx 주소가 이 변수로 주입됩니다.
    db_host = os.environ.get('DB_HOST')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_name = os.environ.get('DB_NAME')
    if db_host:
        print(f"\n[DEBUG] 현재 접속을 시도하는 엔드포인트: {db_host}")
        if "ap-northeast-2" in db_host:
            print("[DEBUG] 결과: 서울 리전 Proxy로 판명됨")
        elif "us-west-2" in db_host:
            print("[DEBUG] 결과: 오리건 리전 Proxy로 판명됨")
    if not db_host:
        raise ValueError("[ERROR] DB_HOST 환경 변수가 설정되지 않았습니다.")

    try:
        # RDS Proxy 연결 시 성능과 안정성을 고려한 설정
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=3306,
            cursorclass=DictCursor,
            connect_timeout=5,     # 연결 타임아웃
            autocommit=True        # RDS Proxy 환경에서 트랜잭션 핀 고정 최소화
        )
        print(f"[DB-LOG] 성공적으로 연결됨: {db_host}")
        return connection
    except Exception as e:
        print(f"[DB-ERROR] 연결 실패: {e}")
        raise e
