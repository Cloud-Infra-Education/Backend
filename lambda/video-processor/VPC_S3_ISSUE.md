# VPC 내에서 S3 접근 문제 해결

## 문제 상황

로그에서 `head_object 호출 중...` 이후에 멈추는 현상이 발생했습니다.

## 원인

Lambda 함수가 VPC 내부에 배포되어 있어서:
- S3에 접근하려면 인터넷 게이트웨이를 통해 나가야 함
- NAT Gateway가 필요하거나 VPC 엔드포인트가 필요함
- 이로 인해 S3 접근이 매우 느리거나 타임아웃 발생

## 해결 방법

### 옵션 1: VPC 엔드포인트 생성 (권장)

S3용 VPC 엔드포인트를 생성하여 VPC 내에서 직접 S3에 접근:

```hcl
# Terraform에 추가
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = var.kor_vpc_id
  service_name      = "com.amazonaws.ap-northeast-2.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.private_route_table_ids
}
```

### 옵션 2: 메타데이터 조회를 선택 사항으로 변경

현재 코드는 이미 메타데이터 조회 실패 시 기본값을 사용하도록 되어 있습니다.
타임아웃을 더 짧게 설정하여 빠르게 실패하고 계속 진행하도록 했습니다.

### 옵션 3: NAT Gateway 확인

Lambda가 있는 서브넷에 NAT Gateway가 연결되어 있는지 확인:
- Route Table에 인터넷 게이트웨이 또는 NAT Gateway 경로가 있는지
- Security Group에서 아웃바운드 트래픽이 허용되는지

## 현재 코드 상태

- S3 클라이언트에 타임아웃 설정 추가됨
- `head_object` 실패 시 기본값 사용하도록 처리됨
- 타임아웃: connect_timeout=5초, read_timeout=10초

## 테스트 방법

1. 코드 재배포 (v4 태그)
2. S3에 영상 업로드
3. 로그 확인:
   - `head_object 실패` 메시지가 나오면 VPC 엔드포인트 필요
   - 실패해도 계속 진행되어야 함

## 임시 해결책

메타데이터 조회를 완전히 건너뛰고 파일명만 사용:

```python
# get_s3_metadata 함수를 간소화
def get_s3_metadata(bucket, key):
    filename = os.path.basename(key)
    return {
        'title': os.path.splitext(filename)[0],
        'description': '',
        'age_rating': 'ALL',
        'like_count': 0
    }
```
