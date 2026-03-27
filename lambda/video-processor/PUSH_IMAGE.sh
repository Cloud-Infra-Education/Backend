#!/bin/bash
# ECR에 Docker 이미지 푸시 스크립트

set -e

REGION="ap-northeast-2"
ACCOUNT_ID="404457776061"
REPO_NAME="yuh-video-processor"
IMAGE_TAG="v1"

ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

echo "=== ECR 로그인 ==="
aws ecr get-login-password --region ${REGION} | \
    docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

echo -e "\n=== Docker 이미지 빌드 ==="
docker build -t ${REPO_NAME}:${IMAGE_TAG} .

echo -e "\n=== 이미지 태깅 ==="
docker tag ${REPO_NAME}:${IMAGE_TAG} ${ECR_URI}

echo -e "\n=== ECR에 푸시 ==="
docker push ${ECR_URI}

echo -e "\n✅ 완료! 이미지 URI: ${ECR_URI}"
