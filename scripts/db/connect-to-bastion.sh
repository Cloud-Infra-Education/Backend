#!/bin/bash
# Bastion 인스턴스에 SSH 연결 스크립트

BASTION_DNS="ec2-43-202-55-63.ap-northeast-2.compute.amazonaws.com"
KEY_FILE="/root/y2om-KeyPair-Seoul.pem"
USER="ec2-user"

echo "🔑 Bastion 인스턴스에 연결 중..."
echo "DNS: $BASTION_DNS"
echo "Key: $KEY_FILE"
echo ""

# 키 파일 권한 확인
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ 키 파일이 없습니다: $KEY_FILE"
    exit 1
fi

chmod 400 "$KEY_FILE" 2>/dev/null

# SSH 연결
ssh -i "$KEY_FILE" "$USER@$BASTION_DNS"
