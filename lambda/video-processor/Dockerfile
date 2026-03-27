FROM public.ecr.aws/lambda/python:3.11

# FFmpeg 설치 (정적 바이너리 직접 다운로드)
# Python으로 압축 해제 (tar가 없을 수 있음)
RUN curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o /tmp/ffmpeg.tar.xz && \
    python3 -c "import tarfile; tarfile.open('/tmp/ffmpeg.tar.xz').extractall('/tmp')" && \
    mv /tmp/ffmpeg-*-static/ffmpeg /usr/local/bin/ffmpeg && \
    mv /tmp/ffmpeg-*-static/ffprobe /usr/local/bin/ffprobe && \
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe && \
    ln -sf /usr/local/bin/ffmpeg /usr/bin/ffmpeg && \
    ln -sf /usr/local/bin/ffprobe /usr/bin/ffprobe && \
    rm -rf /tmp/ffmpeg* /var/cache/yum/* 2>/dev/null || true

# 설치 확인
RUN /usr/local/bin/ffmpeg -version | head -1 && /usr/local/bin/ffprobe -version | head -1

# Python 의존성 설치
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# sshtunnel의 paramiko.DSSKey 참조 문제 수정
# sshtunnel 0.4.0이 paramiko.DSSKey를 참조하지만, paramiko 2.12+에서는 제거됨
RUN python3 << 'PYEOF'
import sshtunnel
import os
fpath = os.path.dirname(sshtunnel.__file__) + '/sshtunnel.py'
with open(fpath, 'r') as f:
    content = f.read()
content = content.replace("'dsa': paramiko.DSSKey,", "'dsa': getattr(paramiko, 'DSSKey', None),")
with open(fpath, 'w') as f:
    f.write(content)
print('sshtunnel.py patched')
PYEOF

# Lambda 핸들러 코드 복사
COPY app.py ${LAMBDA_TASK_ROOT}

# Lambda 핸들러 설정
CMD [ "app.handler" ]
