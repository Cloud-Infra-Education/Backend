# Alert Service Lambda

Aurora MySQL 데이터베이스의 리소스 사용량을 모니터링하고, 임계치를 초과하면 CloudWatch 알람을 통해 SNS를 거쳐 Slack으로 실시간 경보를 전송하는 서버리스 함수입니다.

## 주요 기능

- **자동 모니터링**: CloudWatch가 RDS 메트릭을 자동 수집
- **임계치 감지**: CPU, 메모리, 연결 수 등 임계치 초과 시 알람 발생
- **실시간 경보**: SNS를 통해 Lambda 트리거 후 Slack으로 즉시 전송
- **상태 추적**: ALARM/OK 상태 변경 시 모두 알림
- **구조화된 메시지**: Slack Block Kit 형식의 읽기 쉬운 경보

## 기술 스택

- **AWS Lambda**: 서버리스 컴퓨팅 (Python 3.11, Container Image)
- **Amazon CloudWatch**: 메트릭 수집 및 알람 관리
- **Amazon SNS**: Pub/Sub 메시징 (알람 → Lambda)
- **AWS Secrets Manager**: Slack Webhook URL 보안 저장
- **Slack Webhook API**: 실시간 경보 전송
- **Terraform**: Infrastructure as Code

자세한 아키텍처는 [ARCHITECTURE.md](./ARCHITECTURE.md)를 참고하세요.

## 아키텍처 흐름

```
RDS Cluster → CloudWatch Metrics → CloudWatch Alarm 
    → SNS Topic → Lambda Function → Slack
```

## 모니터링 메트릭

- **CPUUtilization**: CPU 사용률 (%)
- **FreeableMemory**: 사용 가능한 메모리 (Bytes)
- **DatabaseConnections**: 데이터베이스 연결 수

## 알람 설정

현재 설정된 알람:
- **이름**: `OTT-DB-CPU-Utilization-High`
- **메트릭**: CPUUtilization
- **임계치**: 1% (테스트용, 실제로는 80% 등으로 설정)
- **평가 기간**: 1분
- **통계**: Average

## Slack 메시지 형식

### ALARM 상태 (위험)
- 🚨 이모지
- 빨간색 (#eb4034)
- 메시지: "상태가 *ALARM*로 변경되었습니다."

### OK 상태 (복구)
- ✅ 이모지
- 초록색 (#2eb886)
- 메시지: "상태가 *OK*로 변경되었습니다."

### 메시지 필드
- 대상 리전
- 감시 메트릭
- 임계치
- 발생 시간 (KST)
- 상세 사유

## 배포

### 1. Docker 이미지 빌드 및 푸시

```bash
# 이미지 빌드
docker build -t yuh-alert-service:v1 .

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
    docker login --username AWS --password-stdin \
    404457776061.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 태깅 및 푸시
docker tag yuh-alert-service:v1 \
    404457776061.dkr.ecr.ap-northeast-2.amazonaws.com/yuh-alert-service:v1
docker push 404457776061.dkr.ecr.ap-northeast-2.amazonaws.com/yuh-alert-service:v1
```

### 2. Terraform 적용

```bash
cd ../../Terraform
terraform apply
```

## 설정 요구사항

### 1. Secrets Manager

Slack Webhook URL을 Secrets Manager에 저장해야 합니다:

```bash
aws secretsmanager create-secret \
  --name "{team-name}/slack/webhook" \
  --secret-string '{"webhook_url":"https://hooks.slack.com/services/..."}'
```

또는 기존 Secret 업데이트:
```bash
aws secretsmanager update-secret \
  --secret-id "{team-name}/slack/webhook" \
  --secret-string '{"webhook_url":"https://hooks.slack.com/services/..."}'
```

### 2. Slack Webhook URL 생성

1. Slack 워크스페이스에 앱 추가
2. Incoming Webhooks 활성화
3. Webhook URL 생성
4. Secrets Manager에 저장

## 테스트

### 수동 테스트

SNS 메시지를 시뮬레이션하여 테스트:

```bash
aws sns publish \
  --topic-arn arn:aws:sns:ap-northeast-2:404457776061:{team}-db-alarm-topic \
  --message '{
    "AlarmName": "OTT-DB-CPU-Utilization-High",
    "NewStateValue": "ALARM",
    "NewStateReason": "Threshold Crossed: 1 datapoint [85.5 (12/01/24 16:30:00)] was greater than or equal to the threshold (80.0).",
    "Region": "ap-northeast-2",
    "Trigger": {
      "MetricName": "CPUUtilization",
      "Threshold": 80.0
    }
  }'
```

### CloudWatch 알람 테스트

알람을 수동으로 ALARM 상태로 변경:

```bash
aws cloudwatch set-alarm-state \
  --alarm-name OTT-DB-CPU-Utilization-High \
  --state-value ALARM \
  --state-reason "Manual test"
```

## 모니터링

### CloudWatch Logs

```bash
aws logs tail /aws/lambda/ott-alert-service --follow
```

### 예상 로그

```
슬랙 전송 성공: 200
```

### 에러 로그

```
Secrets Manager 조회 실패: ...
에러 발생: ...
```

## 파일 구조

```
alert-service/
  ├── app.py              # Lambda 핸들러 함수
  ├── Dockerfile          # Docker 이미지 빌드 설정
  ├── requirements.txt    # Python 의존성 (빈 파일)
  ├── README.md           # 이 파일
  └── ARCHITECTURE.md     # 상세 아키텍처 문서
```

## 주요 코드 설명

### Secrets Manager 조회

```python
def get_slack_webhook():
    secret_name = os.environ.get('SECRET_NAME', 'yuh/slack/webhook')
    client = boto3.client('secretsmanager', region_name="ap-northeast-2")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString']).get('webhook_url')
```

### SNS 메시지 파싱

```python
sns_record = event['Records'][0]['Sns']
raw_message = sns_record.get('Message')
msg_json = json.loads(raw_message)
```

### Slack 메시지 전송

```python
slack_payload = {
    "text": f"{emoji} *[OTT 인프라 감지]* 상태가 *{new_state}*로 변경되었습니다.",
    "attachments": [...]
}
req = urllib.request.Request(webhook_url, data=json.dumps(slack_payload).encode('utf-8'))
urllib.request.urlopen(req)
```

## 문제 해결

### Slack 메시지가 전송되지 않는 경우

1. **Secrets Manager 확인:**
   ```bash
   aws secretsmanager get-secret-value --secret-id {team}/slack/webhook
   ```

2. **Lambda 로그 확인:**
   ```bash
   aws logs tail /aws/lambda/ott-alert-service --follow
   ```

3. **Webhook URL 유효성 확인:**
   - Slack 앱 설정에서 Webhook URL 확인
   - URL이 활성화되어 있는지 확인

### 알람이 트리거되지 않는 경우

1. **CloudWatch Alarm 상태 확인:**
   ```bash
   aws cloudwatch describe-alarms --alarm-names OTT-DB-CPU-Utilization-High
   ```

2. **SNS Subscription 확인:**
   ```bash
   aws sns list-subscriptions-by-topic --topic-arn {topic-arn}
   ```

3. **Lambda 권한 확인:**
   ```bash
   aws lambda get-policy --function-name ott-alert-service
   ```

## 참고 자료

- [CloudWatch Alarms 문서](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html)
- [SNS Lambda Integration](https://docs.aws.amazon.com/sns/latest/dg/sns-lambda.html)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
