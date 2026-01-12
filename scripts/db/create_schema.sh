#!/bin/bash
# ERD 기반 데이터베이스 스키마 생성 스크립트

DB_HOST="y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com"
DB_USER="proxy_admin"
DB_PASSWORD="test1234"
DB_NAME="ott_db"

# 스크립트 위치 기준으로 SQL 파일 경로 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="$SCRIPT_DIR/../../sql/schema.sql"

echo "=========================================="
echo "ERD 기반 데이터베이스 스키마 생성"
echo "=========================================="
echo "RDS 클러스터: $DB_HOST"
echo "데이터베이스: $DB_NAME"
echo "SQL 파일: $SQL_FILE"
echo ""

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ SQL 파일을 찾을 수 없습니다: $SQL_FILE"
    exit 1
fi

# MySQL 클라이언트로 SQL 스크립트 실행
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 스키마 생성 완료!"
    echo ""
    echo "생성된 테이블:"
    echo "  - users"
    echo "  - contents"
    echo "  - contents_likes"
    echo "  - watch_history"
    echo "  - video_assets"
else
    echo ""
    echo "❌ 스키마 생성 실패"
    exit 1
fi
