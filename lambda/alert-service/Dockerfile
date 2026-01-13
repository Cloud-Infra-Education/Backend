# 위치: Backend/lambda/alert-service/Dockerfile

FROM public.ecr.aws/lambda/python:3.11

# 1. 의존성 라이브러리 설치
# (현재 코드에서 boto3는 기본 내장, 별도 라이브러리 없으면 requirements.txt는 빈 파일)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. 실행 코드 복사
COPY app.py ${LAMBDA_TASK_ROOT}/

# 3. 실행 핸들러 설정
CMD ["app.handler"]
