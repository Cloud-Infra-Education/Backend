# 위치: Backend/lambda/video-processor/Dockerfile

FROM public.ecr.aws/lambda/python:3.11

# 1. FFmpeg 설치 (바이너리 직접 다운로드 방식)
RUN yum update -y && \
    yum install -y tar xz && \
    curl https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o ffmpeg.tar.xz && \
    tar -xf ffmpeg.tar.xz && \
    mv ffmpeg-*-amd64-static/ffmpeg /usr/bin/ffmpeg && \
    mv ffmpeg-*-amd64-static/ffprobe /usr/bin/ffprobe && \
    rm -rf ffmpeg*

# 2. 의존성 라이브러리 설치 (pymysql 등)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. [수정] 실행 코드만 복사 (security.py 제외)
COPY app.py ${LAMBDA_TASK_ROOT}/

# 4. 실행 핸들러 설정
CMD ["app.handler"]
