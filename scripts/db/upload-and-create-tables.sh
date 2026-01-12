#!/bin/bash
# Bastion 인스턴스에 SQL 스크립트를 업로드하고 실행하는 스크립트

BASTION_DNS="ec2-43-202-55-63.ap-northeast-2.compute.amazonaws.com"
KEY_FILE="/root/y2om-KeyPair-Seoul.pem"
USER="ec2-user"
SQL_FILE="/root/Backend/create_tables.sql"
SCRIPT_FILE="/root/Backend/create_tables.sh"
REMOTE_SQL="~/create_tables.sql"
REMOTE_SCRIPT="~/create_tables.sh"

echo "📤 SQL 스크립트와 실행 스크립트를 Bastion에 업로드 중..."
scp -i "$KEY_FILE" "$SQL_FILE" "$USER@$BASTION_DNS:$REMOTE_SQL"
scp -i "$KEY_FILE" "$SCRIPT_FILE" "$USER@$BASTION_DNS:$REMOTE_SCRIPT"

if [ $? -ne 0 ]; then
    echo "❌ 파일 업로드 실패"
    exit 1
fi

echo "✅ 파일 업로드 완료"
echo ""
echo "🚀 Bastion에서 테이블 생성 스크립트 실행 중..."
ssh -i "$KEY_FILE" "$USER@$BASTION_DNS" "chmod +x $REMOTE_SCRIPT && $REMOTE_SCRIPT"
