#!/bin/bash
# ERD 기반 테이블 생성 스크립트

DB_HOST="y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com"
DB_USER="proxy_admin"
DB_PASSWORD="test1234"
DB_NAME="ott_db"
SQL_FILE="${HOME}/create_tables.sql"

echo "=========================================="
echo "ERD 기반 데이터베이스 테이블 생성"
echo "=========================================="
echo "RDS 클러스터: $DB_HOST"
echo "데이터베이스: $DB_NAME"
echo ""

# MySQL 클라이언트로 SQL 스크립트 실행
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 테이블 생성 완료!"
    echo ""
    echo "생성된 테이블:"
    echo "  - users (수정됨)"
    echo "  - contents"
    echo "  - contents_likes"
    echo "  - watch_history"
    echo "  - video_assets"
else
    echo ""
    echo "❌ 테이블 생성 실패"
    exit 1
fi
