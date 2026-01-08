# 1. 가볍고 빠른 Python 3.11 이미지를 베이스로 사용합니다.
FROM python:3.11-slim

# 2. 컨테이너 내 작업 디렉토리를 설정합니다.
WORKDIR /app

# 3. 의존성 파일을 먼저 복사하여 빌드 속도를 높입니다.
COPY users/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 공통 모듈(common)과 유저 서비스 코드(users)를 각각 복사합니다.
# 주의: 빌드 시 'Backend/app' 경로에서 실행해야 합니다.
COPY common/ /app/common/
COPY users/ /app/users/

# 5. 환경 변수 기본값 설정 (실제 값은 EKS 배포 시 주입됩니다).
ENV REGION_NAME=seoul
ENV PYTHONPATH=/app

# 6. 서버 실행 명령 (uvicorn 사용)
CMD ["uvicorn", "users.app:app", "--host", "0.0.0.0", "--port", "8000"]
