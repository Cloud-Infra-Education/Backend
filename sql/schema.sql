-- ============================================================
-- OTT 플랫폼 데이터베이스 스키마 (ERD 기반)
-- ============================================================

USE ott_db;

-- ============================================================
-- 1. users 테이블 (사용자)
-- ============================================================
-- ERD 필드: id, email, password_hash, region_code, subscription_status, created_at

DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    region_code VARCHAR(100),
    subscription_status VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_region_code (region_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. contents 테이블 (컨텐츠메인)
-- ============================================================
-- ERD 필드: id, title, description, age_rating, like_count

DROP TABLE IF EXISTS contents;
CREATE TABLE contents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    age_rating VARCHAR(50),
    like_count INT DEFAULT 0,
    INDEX idx_title (title),
    INDEX idx_age_rating (age_rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. contents_likes 테이블 (좋아요 상세)
-- ============================================================
-- ERD 필드: id, user_id, contents_id

DROP TABLE IF EXISTS contents_likes;
CREATE TABLE contents_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    contents_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (contents_id) REFERENCES contents(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_content_like (user_id, contents_id),
    INDEX idx_user_id (user_id),
    INDEX idx_contents_id (contents_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. watch_history 테이블 (시청기록)
-- ============================================================
-- ERD 필드: id, user_id, content_id, last_played_time, updated_at

DROP TABLE IF EXISTS watch_history;
CREATE TABLE watch_history (
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
-- 5. video_assets 테이블 (영상 파일 정보)
-- ============================================================
-- ERD 필드: id, content_id, video_url, duration

DROP TABLE IF EXISTS video_assets;
CREATE TABLE video_assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    video_url VARCHAR(512) NOT NULL,
    duration INT COMMENT '영상 길이 (초 단위)',
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    INDEX idx_content_id (content_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 테이블 생성 확인
-- ============================================================

SHOW TABLES;
