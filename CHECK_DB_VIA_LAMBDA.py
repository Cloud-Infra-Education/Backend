#!/usr/bin/env python3
"""
Lambda를 통해 DB 확인 (간접 방법)
CloudWatch Logs에서 최근 실행 결과 확인
"""
import boto3
import json
from datetime import datetime, timedelta

def check_lambda_logs():
    """CloudWatch Logs에서 Lambda 실행 결과 확인"""
    logs_client = boto3.client('logs', region_name='ap-northeast-2')
    function_name = 'formation-lap-video-processor'
    log_group = f'/aws/lambda/{function_name}'
    
    # 최근 1시간 로그 조회
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
    
    try:
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            filterPattern='성공 OR 완료 OR contents OR video_assets'
        )
        
        print("=" * 50)
        print("최근 Lambda 실행 로그 (DB 저장 관련)")
        print("=" * 50)
        
        events = response.get('events', [])
        if events:
            for event in events[-20:]:  # 최근 20개
                message = event['message']
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        else:
            print("❌ 최근 로그가 없습니다.")
            print("\n다른 방법:")
            print("1. CloudWatch Logs 콘솔에서 확인")
            print("2. 또는 S3에 비디오를 다시 업로드하여 테스트")
        
    except Exception as e:
        print(f"❌ 로그 조회 실패: {e}")

def check_via_sql_query():
    """SQL 쿼리를 Lambda로 실행 (고급 방법)"""
    print("\n" + "=" * 50)
    print("DB 직접 확인 방법")
    print("=" * 50)
    print("""
다음 중 하나의 방법을 사용하세요:

1. CloudWatch Logs Insights 사용:
   aws logs start-query \\
     --log-group-name /aws/lambda/formation-lap-video-processor \\
     --start-time $(date -d '1 hour ago' +%s) \\
     --end-time $(date +%s) \\
     --query-string "fields @timestamp, @message | filter @message like /성공|완료|contents|video_assets/"

2. MySQL 클라이언트 (VPC 내부 또는 Bastion):
   mysql -h formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \\
         -u admin -ptest1234 ott_db \\
         -e "SELECT * FROM contents; SELECT * FROM video_assets;"

3. AWS RDS Data API 사용 (구현 필요)

4. FastAPI 엔드포인트로 확인:
   curl http://video-service.formation-lap.svc.cluster.local:8000/videos/search/
    """)

if __name__ == "__main__":
    check_lambda_logs()
    check_via_sql_query()
