# API 접속 가이드

## 서버 실행 방법

### 방법 1: Python 직접 실행
```bash
cd /root/Backend
python main.py
```

### 방법 2: uvicorn 명령어 사용
```bash
cd /root/Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 방법 3: 실행 스크립트 사용
```bash
cd /root/Backend
./run_server.sh
```

## 웹브라우저에서 접속하는 방법

### 1. API 문서 (Swagger UI) - 추천!
서버 실행 후 브라우저에서 다음 주소로 접속:
```
http://localhost:8000/docs
```

이 페이지에서:
- 모든 API 엔드포인트를 확인할 수 있습니다
- 각 API를 테스트할 수 있습니다 ("Try it out" 버튼 클릭)
- API 요청/응답 예제를 확인할 수 있습니다

### 2. ReDoc 문서
```
http://localhost:8000/redoc
```

### 3. API 직접 접속 (GET 요청만 가능)

#### 루트 엔드포인트
```
http://localhost:8000/
```

#### 헬스 체크 (데이터베이스 연결 확인)
```
http://localhost:8000/search/health
```

#### 검색 API (예시)
```
http://localhost:8000/search/search?q=test&limit=10&offset=0
```

## 사용 가능한 엔드포인트

### 검색 API
- **URL**: `/search/search`
- **Method**: GET
- **파라미터**:
  - `q` (필수): 검색어
  - `limit` (선택, 기본값: 10): 결과 개수 제한 (1-100)
  - `offset` (선택, 기본값: 0): 페이지 오프셋
- **예시**: `http://localhost:8000/search/search?q=사용자&limit=20&offset=0`

### 헬스 체크 API
- **URL**: `/search/health`
- **Method**: GET
- **응답**: 데이터베이스 연결 상태 및 리전 정보

## 환경변수 설정

서버 실행 전에 다음 환경변수를 설정해야 합니다:

```bash
export DB_HOST="your-rds-proxy-endpoint.ap-northeast-2.rds.amazonaws.com"
export DB_USER="your-db-user"
export DB_PASSWORD="your-db-password"
export DB_NAME="your-db-name"
export DB_PORT="3306"  # 선택사항, 기본값: 3306
export REGION_NAME="ap-northeast-2"  # 또는 "us-west-2"
```

또는 `.env` 파일을 생성:
```env
DB_HOST=your-rds-proxy-endpoint.ap-northeast-2.rds.amazonaws.com
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-db-name
DB_PORT=3306
REGION_NAME=ap-northeast-2
```

## 문제 해결

### 포트가 이미 사용 중인 경우
다른 포트를 사용하세요:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 데이터베이스 연결 오류
1. 환경변수가 올바르게 설정되었는지 확인
2. RDS Proxy 엔드포인트가 올바른지 확인
3. 보안 그룹 설정 확인

### 모듈을 찾을 수 없는 경우
```bash
cd /root/Backend
pip install -r requirements.txt
```
