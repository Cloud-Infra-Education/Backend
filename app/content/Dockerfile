FROM python:3.11-slim

WORKDIR /app

# 필수 패키지 설치 및 의존성 설치
COPY content/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY common/ /app/common/
COPY content/ /app/content/

ENV REGION_NAME=ap-northeast-2
ENV PYTHONPATH=/app

# uvicorn을 python 모듈로 실행하면 PATH 문제를 피할 수 있습니다.
CMD ["python3", "-m", "uvicorn", "content.app:app", "--host", "0.0.0.0", "--port", "8000"]
