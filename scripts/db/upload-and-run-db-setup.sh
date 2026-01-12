#!/bin/bash
# Bastion 인스턴스에 데이터베이스 설정 스크립트를 업로드하고 실행하는 스크립트

BASTION_DNS="ec2-43-202-55-63.ap-northeast-2.compute.amazonaws.com"
KEY_FILE="/root/y2om-KeyPair-Seoul.pem"
USER="ec2-user"
SETUP_SCRIPT="/root/Backend/setup-database.sh"
REMOTE_SCRIPT="~/setup-database.sh"

echo "📤 데이터베이스 설정 스크립트를 Bastion에 업로드 중..."
scp -i "$KEY_FILE" "$SETUP_SCRIPT" "$USER@$BASTION_DNS:$REMOTE_SCRIPT"

if [ $? -ne 0 ]; then
    echo "❌ 스크립트 업로드 실패"
    exit 1
fi

echo "✅ 스크립트 업로드 완료"
echo ""
echo "🚀 Bastion에서 데이터베이스 설정 스크립트 실행 중..."
ssh -i "$KEY_FILE" "$USER@$BASTION_DNS" "chmod +x $REMOTE_SCRIPT && $REMOTE_SCRIPT"
