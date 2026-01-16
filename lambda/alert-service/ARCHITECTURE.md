# Alert Service Lambda 아키텍처 및 기술 스택

## 개요

Aurora MySQL 데이터베이스의 리소스 사용량을 모니터링하고, 임계치를 초과하면 CloudWatch 알람을 통해 SNS를 거쳐 Slack으로 실시간 경보를 전송하는 서버리스 함수입니다.

## 아키텍처 다이어그램

```
Aurora MySQL (RDS Cluster)
    ↓ (메트릭 수집)
CloudWatch Metrics
    ↓ (임계치 초과 감지)
CloudWatch Alarm
    ↓ (알람 발생)
SNS Topic (db-alarm-topic)
    ↓ (이벤트 전달)
Lambda Function (alert-service)
    ├─ Secrets Manager에서 Slack Webhook URL 조회
    ├─ SNS 메시지 파싱
    ├─ Slack 메시지 포맷팅
    └─ Slack Webhook API 호출
        ↓
Slack 채널 (실시간 경보 수신)
```

## 기술 스택

### 1. AWS Lambda (서버리스 컴퓨팅)

**역할:**
- SNS 이벤트를 받아 Slack으로 경보 전송
- 서버 관리 없이 자동 스케일링

**구성:**
- **Runtime**: Python 3.11 (Docker Container Image)
- **Package Type**: Container Image (ECR 사용)
- **Memory**: 기본값 (512 MB)
- **Timeout**: 기본값 (3초)
- **VPC Configuration**: 없음 (Public 인터넷 접근 필요 - Slack API 호출)

**주요 기능:**
- SNS 메시지 수신 및 파싱
- Secrets Manager에서 Slack Webhook URL 조회
- Slack 메시지 포맷팅 및 전송

### 2. Amazon CloudWatch (모니터링 및 알람)

**역할:**
- RDS 클러스터의 메트릭 수집 및 모니터링
- 임계치 기반 알람 생성 및 관리

**모니터링 메트릭:**
- **CPUUtilization**: CPU 사용률 (%)
- **FreeableMemory**: 사용 가능한 메모리 (Bytes)
- **DatabaseConnections**: 데이터베이스 연결 수

**알람 설정:**
- **알람 이름**: `OTT-DB-CPU-Utilization-High`
- **평가 기간**: 5분
- **임계치**: 설정 가능 (예: CPU 80% 이상)
- **알람 액션**: SNS Topic으로 전송

**알람 상태:**
- **ALARM**: 임계치 초과 (위험 상태)
- **OK**: 정상 상태 (복구)

### 3. Amazon SNS (Simple Notification Service)

**역할:**
- CloudWatch 알람과 Lambda 함수 간의 이벤트 브릿지
- Pub/Sub 메시징 패턴 구현

**구성:**
- **Topic**: `{team-name}-db-alarm-topic`
- **Subscription**: Lambda 함수 구독
- **메시지 형식**: JSON (CloudWatch 알람 정보 포함)

**메시지 구조:**
```json
{
  "AlarmName": "OTT-DB-CPU-Utilization-High",
  "NewStateValue": "ALARM",
  "NewStateReason": "Threshold Crossed: ...",
  "Region": "ap-northeast-2",
  "Trigger": {
    "MetricName": "CPUUtilization",
    "Threshold": 80.0
  }
}
```

### 4. AWS Secrets Manager (시크릿 관리)

**역할:**
- Slack Webhook URL을 안전하게 저장 및 관리
- 코드에 민감한 정보 노출 방지

**구성:**
- **Secret Name**: `{team-name}/slack/webhook`
- **Secret Format**: JSON
  ```json
  {
    "webhook_url": "https://hooks.slack.com/services/..."
  }
  ```

**보안:**
- 암호화된 저장
- IAM 기반 접근 제어
- 자동 로테이션 지원 (선택사항)

### 5. Slack Webhook API (외부 통합)

**역할:**
- 실시간 경보 메시지 수신
- 팀 채널에 알림 전송

**메시지 포맷:**
- **Slack Block Kit** 형식 사용
- **Attachments**를 통한 구조화된 메시지
- **Color Coding**: 
  - 빨강 (#eb4034): ALARM 상태
  - 초록 (#2eb886): OK 상태 (복구)

**메시지 구성 요소:**
- 이모지: 🚨 (알람) / ✅ (복구)
- 제목: 경보 상세 정보
- 필드:
  - 대상 리전
  - 감시 메트릭
  - 임계치
  - 발생 시간 (KST)
  - 상세 사유

### 6. Amazon ECR (Elastic Container Registry)

**역할:**
- Lambda 함수용 Docker 이미지 저장 및 관리

**구성:**
- **Repository**: `yuh-alert-service`
- **Image Tag**: `v1`
- **Image Type**: Container Image (Lambda용)

**이미지 구성:**
- Base Image: `public.ecr.aws/lambda/python:3.11`
- Python 라이브러리: boto3 (기본 내장)
- 추가 의존성: 없음 (표준 라이브러리만 사용)

### 7. IAM (Identity and Access Management)

**역할:**
- Lambda 함수 실행 권한 관리
- 리소스 접근 권한 제어

**권한 구성:**

**기본 역할:**
- Lambda 기본 실행 역할

**커스텀 정책:**
- **Secrets Manager 권한:**
  - `secretsmanager:GetSecretValue`: Webhook URL 조회
  - Resource: 특정 Secret ARN

**SNS 권한:**
- Lambda 함수가 SNS Topic에서 메시지를 받을 수 있도록 설정
- `aws_lambda_permission` 리소스로 SNS → Lambda 호출 허용

### 8. Terraform (Infrastructure as Code)

**역할:**
- 인프라 자동화 및 관리
- 재현 가능한 인프라 구성

**생성 리소스:**
- CloudWatch Alarm
- SNS Topic 및 Subscription
- Lambda 함수
- IAM 역할 및 정책
- Lambda 권한 설정

**모듈 구조:**
```
Terraform/modules/cloudwatch/
  ├── alarm.tf              # CloudWatch 알람 설정
  ├── sns.tf                # SNS Topic 및 Subscription
  ├── lambda_alert.tf       # Lambda 함수 및 권한
  ├── iam-role.tf           # IAM 역할 및 정책
  ├── secrets-manager.tf    # Secrets Manager 데이터 소스
  ├── variables.tf          # 입력 변수
  └── versions.tf           # Provider 버전
```

## 데이터 흐름

### 1. 메트릭 수집
```
Aurora MySQL (RDS Cluster)
    ↓ (자동 수집)
CloudWatch Metrics
    - CPUUtilization
    - FreeableMemory
    - DatabaseConnections
```

### 2. 알람 평가
```
CloudWatch Alarm
    ├─ 평가 기간: 5분
    ├─ 임계치: CPU 80% 이상
    └─ 상태 변경 감지
```

### 3. 알람 발생
```
CloudWatch Alarm (ALARM 상태)
    ↓ (알람 액션)
SNS Topic
    └─ JSON 메시지 발행
```

### 4. Lambda 트리거
```
SNS Topic
    ↓ (이벤트 전달)
Lambda Function (alert-service)
    ├─ SNS 메시지 수신
    └─ Records[0]['Sns'] 파싱
```

### 5. 시크릿 조회
```
Lambda Function
    ↓ (Secrets Manager API 호출)
AWS Secrets Manager
    └─ Slack Webhook URL 반환
```

### 6. 메시지 포맷팅
```
Lambda Function
    ├─ SNS 메시지 파싱
    │   ├─ AlarmName
    │   ├─ NewStateValue (ALARM/OK)
    │   ├─ MetricName
    │   ├─ Threshold
    │   └─ Reason
    ├─ 시간 변환 (UTC → KST)
    └─ Slack 메시지 포맷 생성
```

### 7. Slack 전송
```
Lambda Function
    ↓ (HTTP POST)
Slack Webhook API
    ↓
Slack 채널 (실시간 경보 표시)
```

## 메시지 포맷 상세

### Slack 메시지 구조

```json
{
  "text": "🚨 *[OTT 인프라 감지]* 상태가 *ALARM*로 변경되었습니다.",
  "attachments": [
    {
      "color": "#eb4034",
      "title": "경보 상세: OTT-DB-CPU-Utilization-High",
      "fields": [
        {"title": "대상 리전", "value": "ap-northeast-2", "short": true},
        {"title": "감시 메트릭", "value": "CPUUtilization", "short": true},
        {"title": "임계치", "value": "80%", "short": true},
        {"title": "발생 시간", "value": "2024-01-12 16:30:00 KST", "short": true},
        {"title": "상세 사유", "value": "Threshold Crossed: ...", "short": false}
      ],
      "footer": "OTT 플랫폼 통합 관제 시스템",
      "ts": 1705065000
    }
  ]
}
```

### 상태별 메시지

**ALARM 상태 (위험):**
- 이모지: 🚨
- 색상: 빨강 (#eb4034)
- 텍스트: "상태가 *ALARM*로 변경되었습니다."

**OK 상태 (복구):**
- 이모지: ✅
- 색상: 초록 (#2eb886)
- 텍스트: "상태가 *OK*로 변경되었습니다."

## 보안 고려사항

### 1. 시크릿 관리
- Slack Webhook URL을 Secrets Manager에 저장
- 코드에 하드코딩하지 않음
- IAM 기반 접근 제어

### 2. 네트워크 보안
- Lambda 함수는 Public 인터넷 접근 필요 (Slack API 호출)
- VPC 배포 없음 (간단한 아키텍처)

### 3. 접근 제어
- IAM 역할 기반 권한 관리
- 최소 권한 원칙 적용
- Secrets Manager 특정 Secret만 접근 가능

## 성능 최적화

### 1. 비동기 처리
- SNS 기반 비동기 이벤트 처리
- 사용자 요청과 분리된 백그라운드 처리

### 2. 빠른 응답
- 단순한 메시지 포맷팅 및 전송
- 외부 의존성 최소화 (boto3만 사용)
- 실행 시간: 보통 1-2초 이내

### 3. 리소스 효율
- 최소 메모리 할당 (기본값 사용)
- 짧은 타임아웃 (기본값 사용)

## 확장성

### 1. 다중 알람 지원
- 하나의 Lambda 함수가 여러 알람 처리
- SNS Topic에 여러 알람이 구독 가능

### 2. 다중 채널 지원
- Secrets Manager에 여러 Webhook URL 저장 가능
- 코드 수정으로 여러 채널에 전송 가능

### 3. 자동 스케일링
- Lambda 함수는 자동으로 동시 실행 수 증가
- SNS 메시지 수에 따라 자동 확장

## 모니터링 및 로깅

### 1. CloudWatch Logs
- 모든 실행 로그 자동 수집
- 에러 추적 및 디버깅

### 2. 로그 레벨
- INFO: 정상 처리 (슬랙 전송 성공)
- ERROR: 처리 실패 (Secrets Manager 조회 실패, Slack 전송 실패)

### 3. 주요 로그
```
슬랙 전송 성공: 200
Secrets Manager 조회 실패: ...
에러 발생: ...
```

## 에러 처리

### 1. Secrets Manager 조회 실패
- 명확한 에러 메시지 로깅
- 예외 발생 시 Lambda 실패 처리

### 2. Slack 전송 실패
- HTTP 에러 코드 로깅
- 예외 발생 시 Lambda 실패 처리
- SNS 재시도 메커니즘 활용 가능

### 3. 메시지 파싱 실패
- JSON 파싱 에러 처리
- 기본값 사용 또는 에러 로깅

## 배포 프로세스

### 1. Docker 이미지 빌드
```bash
docker build -t yuh-alert-service:v1 .
```

### 2. ECR에 푸시
```bash
docker tag yuh-alert-service:v1 {ECR_URI}/yuh-alert-service:v1
docker push {ECR_URI}/yuh-alert-service:v1
```

### 3. Terraform 적용
```bash
terraform apply
```

### 4. 자동 배포
- Terraform이 Lambda 함수 생성/업데이트
- SNS Subscription 자동 설정
- IAM 권한 자동 구성
- CloudWatch Alarm 자동 생성

## 주요 파일 구조

```
Backend/lambda/alert-service/
  ├── app.py              # Lambda 핸들러 함수
  ├── Dockerfile          # Docker 이미지 빌드 설정
  ├── requirements.txt    # Python 의존성 (빈 파일)
  └── ARCHITECTURE.md     # 이 문서
```

## 기술 선택 이유

### 1. Lambda (서버리스)
- **이유**: 알람 발생이 불규칙적이므로 서버리스가 적합
- **장점**: 사용한 만큼만 비용 지불, 자동 스케일링

### 2. SNS (Pub/Sub)
- **이유**: CloudWatch와 Lambda 간 느슨한 결합
- **장점**: 확장성, 다중 구독자 지원, 재시도 메커니즘

### 3. Secrets Manager
- **이유**: Webhook URL 같은 민감한 정보 보안 관리
- **장점**: 암호화, IAM 기반 접근 제어, 자동 로테이션

### 4. Slack Webhook
- **이유**: 팀 협업 도구와의 실시간 통합
- **장점**: 즉시 알림, 구조화된 메시지, 이모지/색상 지원

### 5. Container Image
- **이유**: 일관된 배포 환경
- **장점**: 로컬과 프로덕션 환경 일치

## 알람 설정 예시

### CPU 사용률 알람
- **메트릭**: CPUUtilization
- **임계치**: 80%
- **평가 기간**: 5분
- **통계**: Average

### 메모리 부족 알람
- **메트릭**: FreeableMemory
- **임계치**: 특정 바이트 이하
- **평가 기간**: 5분
- **통계**: Minimum

### 연결 수 알람
- **메트릭**: DatabaseConnections
- **임계치**: 특정 개수 이상
- **평가 기간**: 5분
- **통계**: Maximum

## 사용 시나리오

### 시나리오 1: CPU 사용률 급증
1. DB 쿼리 부하 증가
2. CPUUtilization 80% 초과
3. CloudWatch Alarm 발동
4. SNS를 통해 Lambda 트리거
5. Slack에 빨간색 경보 메시지 전송
6. 팀원 즉시 인지 및 대응

### 시나리오 2: 메모리 부족
1. 메모리 사용량 증가
2. FreeableMemory 임계치 이하
3. CloudWatch Alarm 발동
4. Slack에 경보 전송
5. DBA 또는 DevOps 팀 조치

### 시나리오 3: 문제 해결 후 복구
1. 문제 해결로 메트릭 정상화
2. CloudWatch Alarm 상태 OK로 변경
3. Slack에 초록색 복구 메시지 전송
4. 팀원 문제 해결 확인

## 모니터링 체크리스트

- [ ] CloudWatch Alarm이 올바르게 생성되었는가?
- [ ] SNS Topic에 Lambda가 구독되었는가?
- [ ] Lambda 함수에 Secrets Manager 권한이 있는가?
- [ ] Slack Webhook URL이 Secrets Manager에 저장되었는가?
- [ ] 테스트 알람으로 메시지가 전송되는가?

## 향후 개선 사항

1. **다중 채널 지원**: Slack 외에 Email, SMS 등 추가
2. **알람 그룹핑**: 비슷한 알람을 묶어서 전송
3. **알람 억제**: 짧은 시간 내 반복 알람 방지
4. **대시보드 연동**: CloudWatch Dashboard와 연동
5. **메트릭 히스토리**: 알람 이력 데이터베이스 저장
