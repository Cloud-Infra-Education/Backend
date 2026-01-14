#!/bin/bash
# 간단한 DB 확인 스크립트

DB_HOST="formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com"
DB_USER="admin"
DB_PASSWORD="test1234"
DB_NAME="ott_db"

echo "=========================================="
echo "DB 테이블 확인"
echo "=========================================="

# contents 테이블
echo ""
echo "📋 contents 테이블:"
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT id, title, age_rating, like_count 
FROM contents 
ORDER BY id DESC 
LIMIT 5;
" 2>/dev/null || echo "⚠️  DB 연결 실패 (VPC 내부 접근 필요)"

# video_assets 테이블
echo ""
echo "🎬 video_assets 테이블:"
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT id, content_id, duration, SUBSTRING(video_url, 1, 50) as video_url_short
FROM video_assets 
ORDER BY id DESC 
LIMIT 5;
" 2>/dev/null || echo "⚠️  DB 연결 실패 (VPC 내부 접근 필요)"

# 조인 쿼리
echo ""
echo "🔗 조인 쿼리 (contents + video_assets):"
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT 
    c.id,
    c.title,
    c.age_rating,
    va.duration,
    CASE WHEN va.video_url IS NOT NULL THEN '✅' ELSE '❌' END as has_video
FROM contents c
LEFT JOIN video_assets va ON c.id = va.content_id
ORDER BY c.id DESC
LIMIT 5;
" 2>/dev/null || echo "⚠️  DB 연결 실패 (VPC 내부 접근 필요)"

echo ""
echo "=========================================="
echo "💡 DB 연결이 안 되면:"
echo "1. VPC 내부 EC2에서 실행하거나"
echo "2. CloudWatch Logs로 확인 (이미 성공 확인됨)"
echo "=========================================="
