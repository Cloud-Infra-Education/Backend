# 1. 파이썬 3.10 버전의 가벼운 이미지로 시작합니다.
FROM python:3.10-slim

# 2. 컨테이너 내부의 작업 폴더를 /app으로 정합니다.
WORKDIR /app

# 3. 필요한 라이브러리 목록을 복사하고 설치합니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 우리 소스 코드를 통째로 컨테이너 안으로 복사합니다.
COPY . .

# 5. FastAPI 서버를 실행합니다. (8000 포트)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
