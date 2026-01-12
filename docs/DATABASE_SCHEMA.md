# 데이터베이스 스키마 문서 (ERD 기반)

## 📊 테이블 구조

ERD 이미지를 기반으로 다음 테이블들이 정의되어 있습니다.

### 1. users (사용자)

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | INT | PK, AUTO_INCREMENT | 사용자 ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 이메일 주소 |
| password_hash | VARCHAR(255) | NOT NULL | 비밀번호 해시 |
| region_code | VARCHAR(100) | | 지역 코드 |
| subscription_status | VARCHAR(50) | DEFAULT 'free' | 구독 상태 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 생성일시 |

### 2. contents (컨텐츠메인)

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | INT | PK, AUTO_INCREMENT | 컨텐츠 ID |
| title | VARCHAR(255) | NOT NULL | 제목 |
| description | TEXT | | 설명 |
| age_rating | VARCHAR(50) | | 연령 등급 |
| like_count | INT | DEFAULT 0 | 좋아요 수 |

### 3. contents_likes (좋아요 상세)

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | INT | PK, AUTO_INCREMENT | 좋아요 ID |
| user_id | INT | FK -> users.id, NOT NULL | 사용자 ID |
| contents_id | INT | FK -> contents.id, NOT NULL | 컨텐츠 ID |
| UNIQUE KEY | (user_id, contents_id) | | 중복 좋아요 방지 |

### 4. watch_history (시청기록)

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | INT | PK, AUTO_INCREMENT | 시청기록 ID |
| user_id | INT | FK -> users.id, NOT NULL | 사용자 ID |
| content_id | INT | FK -> contents.id, NOT NULL | 컨텐츠 ID |
| last_played_time | INT | DEFAULT 0 | 마지막 재생 위치 (초) |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE | 업데이트일시 |
| UNIQUE KEY | (user_id, content_id) | | 사용자별 컨텐츠별 하나의 기록만 |

### 5. video_assets (영상 파일 정보)

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | INT | PK, AUTO_INCREMENT | 영상 파일 ID |
| content_id | INT | FK -> contents.id, NOT NULL | 컨텐츠 ID |
| video_url | VARCHAR(512) | NOT NULL | 영상 URL |
| duration | INT | | 영상 길이 (초) |

## 🔗 테이블 관계

1. **users ↔ contents_likes**: 1:N (한 사용자가 여러 컨텐츠를 좋아요)
2. **contents ↔ contents_likes**: 1:N (한 컨텐츠가 여러 좋아요를 받음)
3. **users ↔ watch_history**: 1:N (한 사용자가 여러 시청기록을 가짐)
4. **contents ↔ watch_history**: 1:N (한 컨텐츠가 여러 시청기록에 기록됨)
5. **contents ↔ video_assets**: 1:N (한 컨텐츠가 여러 영상 파일을 가질 수 있음)

## 📝 스키마 생성 방법

```bash
# Bastion을 통해 스키마 생성
./scripts/db/deploy_schema.sh

# 또는 직접 실행
./scripts/db/create_schema.sh
```

## 🔍 확인 명령어

```bash
# 모든 테이블 목록 확인
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' ott_db -e "SHOW TABLES;"

# 특정 테이블 구조 확인
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' ott_db -e "DESCRIBE users;"
```
