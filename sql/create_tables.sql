-- ============================================================
-- OTT 플랫폼 데이터베이스 스키마 생성 스크립트
-- ============================================================

USE ott_db;

-- ============================================================
-- 1. users 테이블 수정 (기존 테이블이 있으므로 ALTER TABLE 사용)
-- ============================================================

-- 기존 users 테이블 확인 후 필요시 컬럼 추가/수정
-- 기존: id, email, password, last_region, created_at, updated_at
-- ERD: id, email, password_hash, region_code, subscription_status, created_at

-- password를 password_hash로 변경 (데이터 타입 유지)
ALTER TABLE users CHANGE COLUMN password password_hash VARCHAR(255) NOT NULL;

-- last_region을 region_code로 변경
ALTER TABLE users CHANGE COLUMN last_region region_code VARCHAR(100);

-- subscription_status 컬럼 추가
ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50) DEFAULT 'free' AFTER region_code;

-- updated_at 컬럼이 없으면 추가 (기존에 있으므로 생략 가능하지만 확인용)
-- ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- ============================================================
-- 2. contents 테이블 생성 (컨텐츠메인)
-- ============================================================

CREATE TABLE IF NOT EXISTS contents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    age_rating VARCHAR(50),
    like_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_title (title),
    INDEX idx_age_rating (age_rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. contents_likes 테이블 생성 (좋아요 상세)
-- ============================================================

CREATE TABLE IF NOT EXISTS contents_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    contents_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (contents_id) REFERENCES contents(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_content_like (user_id, contents_id),
    INDEX idx_user_id (user_id),
    INDEX idx_contents_id (contents_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. watch_history 테이블 생성 (시청기록)
-- ============================================================

CREATE TABLE IF NOT EXISTS watch_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content_id INT NOT NULL,
    last_played_time INT DEFAULT 0 COMMENT '마지막 재생 위치 (초 단위)',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_content_watch (user_id, content_id),
    INDEX idx_user_id (user_id),
    INDEX idx_content_id (content_id),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. video_assets 테이블 생성 (영상 파일 정보)
-- ============================================================

CREATE TABLE IF NOT EXISTS video_assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    video_url VARCHAR(512) NOT NULL,
    duration INT COMMENT '영상 길이 (초 단위)',
    quality VARCHAR(50) COMMENT '화질 (1080p, 720p, 480p 등)',
    file_size BIGINT COMMENT '파일 크기 (바이트)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    INDEX idx_content_id (content_id),
    INDEX idx_quality (quality)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 테이블 생성 확인
-- ============================================================

SHOW TABLES;

-- 테이블 구조 확인
DESCRIBE users;
DESCRIBE contents;
DESCRIBE contents_likes;
DESCRIBE watch_history;
DESCRIBE video_assets;
