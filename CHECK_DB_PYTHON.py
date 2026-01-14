#!/usr/bin/env python3
"""
DB 테이블 확인 스크립트 (Python 버전)
VPC 내부에서 실행하거나, RDS Proxy에 접근 가능한 환경에서 실행
"""
import pymysql
import os
import sys

# DB 연결 정보
DB_HOST = os.getenv("DB_HOST", "formation-lap-yuh-kor-rds-proxy.proxy-c902seqsaaps.ap-northeast-2.rds.amazonaws.com")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "test1234")
DB_NAME = os.getenv("DB_NAME", "ott_db")

def check_tables():
    try:
        # DB 연결
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            print("=" * 50)
            print("1. contents 테이블 확인")
            print("=" * 50)
            cursor.execute("""
                SELECT 
                    id,
                    title,
                    description,
                    age_rating,
                    like_count,
                    created_at
                FROM contents
                ORDER BY id DESC
                LIMIT 10
            """)
            contents = cursor.fetchall()
            if contents:
                for row in contents:
                    print(f"ID: {row['id']}, Title: {row['title']}, Age Rating: {row['age_rating']}")
                    print(f"  Description: {row['description'][:50]}...")
                    print(f"  Like Count: {row['like_count']}, Created: {row['created_at']}")
                    print()
            else:
                print("❌ contents 테이블이 비어있습니다.")
            print()
            
            print("=" * 50)
            print("2. video_assets 테이블 확인")
            print("=" * 50)
            cursor.execute("""
                SELECT 
                    id,
                    content_id,
                    video_url,
                    thumbnail_url,
                    duration,
                    created_at
                FROM video_assets
                ORDER BY id DESC
                LIMIT 10
            """)
            video_assets = cursor.fetchall()
            if video_assets:
                for row in video_assets:
                    print(f"ID: {row['id']}, Content ID: {row['content_id']}, Duration: {row['duration']}초")
                    print(f"  Video URL: {row['video_url']}")
                    print(f"  Thumbnail URL: {row['thumbnail_url']}")
                    print(f"  Created: {row['created_at']}")
                    print()
            else:
                print("❌ video_assets 테이블이 비어있습니다.")
            print()
            
            print("=" * 50)
            print("3. 조인 쿼리 (contents + video_assets)")
            print("=" * 50)
            cursor.execute("""
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
                LIMIT 10
            """)
            joined = cursor.fetchall()
            if joined:
                for row in joined:
                    print(f"Content ID: {row['id']}, Title: {row['title']}")
                    print(f"  Description: {row['description'][:50]}...")
                    print(f"  Age Rating: {row['age_rating']}, Like Count: {row['like_count']}")
                    if row['video_url']:
                        print(f"  Video URL: {row['video_url']}")
                        print(f"  Thumbnail: {row['thumbnail_url']}")
                        print(f"  Duration: {row['duration']}초")
                    else:
                        print("  ⚠️ video_assets가 없습니다.")
                    print(f"  Created: {row['created_at']}")
                    print()
            else:
                print("❌ 데이터가 없습니다.")
            print()
            
            print("=" * 50)
            print("4. 최근 업로드된 비디오 확인")
            print("=" * 50)
            cursor.execute("""
                SELECT 
                    c.id AS content_id,
                    c.title,
                    c.description,
                    va.video_url,
                    va.duration,
                    va.created_at AS video_uploaded_at
                FROM contents c
                INNER JOIN video_assets va ON c.id = va.content_id
                ORDER BY va.created_at DESC
                LIMIT 5
            """)
            recent = cursor.fetchall()
            if recent:
                for row in recent:
                    print(f"Content ID: {row['content_id']}, Title: {row['title']}")
                    print(f"  Duration: {row['duration']}초")
                    print(f"  Uploaded: {row['video_uploaded_at']}")
                    print()
            else:
                print("❌ 최근 업로드된 비디오가 없습니다.")
        
        conn.close()
        print("=" * 50)
        print("✅ DB 확인 완료!")
        print("=" * 50)
        
    except pymysql.Error as e:
        print(f"❌ DB 연결 실패: {e}")
        print("\n해결 방법:")
        print("1. VPC 내부에서 실행하거나")
        print("2. RDS Proxy에 접근 가능한 환경에서 실행")
        print("3. 또는 Bastion을 통해 접근")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_tables()
