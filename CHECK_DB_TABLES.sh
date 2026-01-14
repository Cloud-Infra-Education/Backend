#!/bin/bash
# DB 테이블 확인 스크립트

set -e

# DB 연결 정보
DB_HOST="${DB_HOST:-formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com}"
DB_USER="${DB_USER:-admin}"
DB_PASSWORD="${DB_PASSWORD:-test1234}"
DB_NAME="${DB_NAME:-ott_db}"

echo "=========================================="
echo "DB 테이블 확인"
echo "=========================================="
echo "DB Host: $DB_HOST"
echo "DB Name: $DB_NAME"
echo ""

# MySQL 클라이언트 확인
if ! command -v mysql &> /dev/null; then
    echo "MySQL 클라이언트가 설치되지 않았습니다."
    echo "설치 중..."
    sudo apt-get update -qq
    sudo apt-get install -y mysql-client -qq
fi

echo "=========================================="
echo "1. contents 테이블 확인"
echo "=========================================="
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT 
    id,
    title,
    description,
    age_rating,
    like_count,
    created_at
FROM contents
ORDER BY id DESC
LIMIT 10;
" 2>/dev/null || echo "❌ DB 연결 실패 (VPC 내부 접근 필요)"

echo ""
echo "=========================================="
echo "2. video_assets 테이블 확인"
echo "=========================================="
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT 
    id,
    content_id,
    video_url,
    thumbnail_url,
    duration,
    created_at
FROM video_assets
ORDER BY id DESC
LIMIT 10;
" 2>/dev/null || echo "❌ DB 연결 실패 (VPC 내부 접근 필요)"

echo ""
echo "=========================================="
echo "3. 조인 쿼리 (contents + video_assets)"
echo "=========================================="
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT 
    c.id,
    c.title,
    c.description,
    c.age_rating,
    c.like_count,
    va.video_url,
    va.thumbnail_url,
    va.duration,
    c.created_at
FROM contents c
LEFT JOIN video_assets va ON c.id = va.content_id
ORDER BY c.id DESC
LIMIT 10;
" 2>/dev/null || echo "❌ DB 연결 실패 (VPC 내부 접근 필요)"

echo ""
echo "=========================================="
echo "4. 최근 업로드된 비디오 확인"
echo "=========================================="
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT 
    c.id AS content_id,
    c.title,
    SUBSTRING(c.description, 1, 50) AS description_short,
    va.video_url,
    va.duration,
    va.created_at AS video_uploaded_at
FROM contents c
INNER JOIN video_assets va ON c.id = va.content_id
ORDER BY va.created_at DESC
LIMIT 5;
" 2>/dev/null || echo "❌ DB 연결 실패 (VPC 내부 접근 필요)"

echo ""
echo "=========================================="
echo "완료!"
echo "=========================================="
