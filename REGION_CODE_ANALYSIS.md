# region_code를 활용한 나라별 구현 분석

## 현재 스키마

### users 테이블
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    region_code ENUM('KOR', 'USA') NOT NULL,  -- ✅ 한국/미국 구분 가능
    subscription_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### contents 테이블
```sql
CREATE TABLE contents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    age_rating VARCHAR(10),  -- ⚠️ 하나의 값만 저장 (예: "12+", "ALL")
    like_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 나라별 구현 가능 여부

### ❌ 현재 구조로는 불가능

**이유:**
- `contents.age_rating`은 하나의 값만 저장
- 한국 등급과 미국 등급을 동시에 저장할 수 없음

### ✅ 가능한 방법들

#### 방법 1: 컬럼 추가 (스키마 변경)
```sql
ALTER TABLE contents 
ADD COLUMN age_rating_kr VARCHAR(10),
ADD COLUMN age_rating_us VARCHAR(10);
```

**장점:**
- 두 나라 등급 모두 저장 가능
- 사용자 region_code에 따라 적절한 등급 반환

**단점:**
- 스키마 변경 필요
- 나라가 늘어나면 컬럼이 계속 늘어남

#### 방법 2: JSON 컬럼 사용
```sql
ALTER TABLE contents 
ADD COLUMN age_ratings JSON;  -- {"KR": "12+", "US": "PG-13"}
```

**장점:**
- 확장성 좋음 (나라 추가 용이)
- 하나의 컬럼으로 관리

**단점:**
- 스키마 변경 필요
- JSON 쿼리 복잡

#### 방법 3: 별도 테이블 (정규화)
```sql
CREATE TABLE content_age_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    region_code ENUM('KOR', 'USA') NOT NULL,
    age_rating VARCHAR(10) NOT NULL,
    FOREIGN KEY (content_id) REFERENCES contents(id)
);
```

**장점:**
- 가장 정규화된 구조
- 나라 추가 용이
- 확장성 최고

**단점:**
- 스키마 변경 필요
- 조인 쿼리 필요

#### 방법 4: 현재 구조 유지 + 사용자 필터링 (가장 간단)

**현재 구조 그대로 사용:**
- `contents.age_rating`에 한국 등급만 저장
- 사용자 `region_code`가 "USA"인 경우:
  - 프론트엔드에서 필터링
  - 또는 API에서 변환 로직 추가

**장점:**
- 스키마 변경 불필요
- 빠른 구현

**단점:**
- 미국 등급 정보 없음
- 정확한 나라별 등급 제공 불가

## 추천 방안

### 옵션 A: 현재 구조 유지 (한국만) ⭐ (가장 빠름)

**구현:**
- TMDB에서 한국(KR) 등급만 가져오기 (현재 구현)
- `contents.age_rating`에 한국 등급 저장
- 사용자 `region_code`는 나중에 확장용으로 보관

**장점:**
- 스키마 변경 없음
- 빠른 구현
- 제출용으로 충분

### 옵션 B: 컬럼 추가 (한국 + 미국)

**구현:**
```sql
ALTER TABLE contents 
ADD COLUMN age_rating_kr VARCHAR(10),
ADD COLUMN age_rating_us VARCHAR(10);
```

**Lambda 코드:**
```python
# TMDB에서 한국, 미국 등급 모두 가져오기
age_rating_kr = get_kr_rating(...)
age_rating_us = get_us_rating(...)

# DB 저장
INSERT INTO contents (..., age_rating_kr, age_rating_us) VALUES (...)
```

**API 응답:**
```python
# 사용자 region_code에 따라 적절한 등급 반환
if user.region_code == "KOR":
    return content.age_rating_kr
elif user.region_code == "USA":
    return content.age_rating_us
```

## 현재 구현 상태

### ✅ 완료된 부분
- TMDB API 연동 (한국 등급만)
- `contents.age_rating`에 한국 등급 저장
- `video_assets`는 Lambda에서 직접 저장 (API 호출 없음)

### ⚠️ 나라별 구현을 원한다면
- 스키마 변경 필요
- Lambda 코드 수정 필요
- API 응답 로직 수정 필요

## 결론

**현재 구조:**
- `users.region_code`는 있지만, `contents.age_rating`은 하나만 저장
- **나라별로 다른 등급을 저장하려면 스키마 변경 필요**

**제출용 추천:**
- 현재 구조 유지 (한국 등급만)
- `users.region_code`는 나중에 확장용으로 보관
- 필요시 나중에 스키마 변경하여 확장 가능
