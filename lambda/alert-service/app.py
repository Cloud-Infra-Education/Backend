import json
import os
import boto3
import urllib.request
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_slack_webhook():
    secret_name = os.environ.get('SECRET_NAME', 'slack/webhook')
    aws_region = os.environ.get('AWS_REGION', 'ap-northeast-2')
    client = boto3.client('secretsmanager', region_name=aws_region)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString']).get('webhook_url')
    except Exception as e:
        logger.error(f"Secrets Manager 조회 실패: {e}")
        raise e

def handler(event, context):
    try:
        webhook_url = get_slack_webhook()
        sns_record = event['Records'][0]['Sns']
        raw_message = sns_record.get('Message')
        msg_json = json.loads(raw_message)

        alarm_name = msg_json.get('AlarmName')
        new_state = msg_json.get('NewStateValue')
        reason = msg_json.get('NewStateReason')
        region = msg_json.get('Region')
        trigger = msg_json.get('Trigger', {})
        metric_name = trigger.get('MetricName')
        threshold = trigger.get('Threshold')
        
        # ⭐ 수정: 메트릭 타입에 따른 이모지 및 리소스 타입 설정
        if 'RDS' in alarm_name or 'Aurora' in alarm_name:
            resource_type = "🗄️ RDS Aurora"
        elif 'EKS' in alarm_name or 'Container' in alarm_name:
            resource_type = "☸️ EKS Cluster"
        else:
            resource_type = "⚠️ 인프라"

        # 한국 시간 변환 (KST)
        kst_time = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S KST')

        color = "#eb4034" if new_state == "ALARM" else "#2eb886" # 위험(빨강) / 복구(초록)
        emoji = "🚨" if new_state == "ALARM" else "✅"

        slack_payload = {
            "text": f"{emoji} *[OTT 인프라 감지]* {resource_type} 상태가 *{new_state}*로 변경되었습니다.",
            "attachments": [
                {
                    "color": color,
                    "title": f"경보 상세: {alarm_name}",
                    "fields": [
                        {"title": "리소스 타입", "value": resource_type, "short": True},  # ⭐ 수정: 리소스 타입 필드 추가
                        {"title": "대상 리전", "value": region, "short": True},
                        {"title": "감시 메트릭", "value": metric_name, "short": True},
                        {"title": "임계치", "value": f"{threshold}%", "short": True},
                        {"title": "발생 시간", "value": kst_time, "short": True},
                        {"title": "상세 사유", "value": f"```{reason}```", "short": False}
                    ],
                    "footer": "OTT 플랫폼 통합 관제 시스템",
                    "ts": datetime.timestamp(datetime.now())
                }
            ]
        }

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(slack_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as res:
            logger.info(f"슬랙 전송 성공: {res.status}")

        return {"status": "success"}
    except Exception as e:
        logger.error(f"에러 발생: {e}")
        raise e

