# Backend 프로젝트

OTT 플랫폼 백엔드 서비스

## 📁 디렉토리 구조

```
Backend/
├── app/                    # 애플리케이션 코드
│   ├── common/            # 공통 모듈
│   └── search/            # 검색 모듈
├── users/                 # 사용자 서비스
├── videos/                # 비디오 서비스
├── docs/                  # 문서
│   ├── API_GUIDE.md
│   ├── DATABASE_SCHEMA.md
│   └── ...
├── scripts/               # 스크립트
│   ├── db/               # 데이터베이스 관련 스크립트
│   ├── deploy/           # 배포 관련 스크립트
│   └── run_server.sh     # 서버 실행 스크립트
├── sql/                   # SQL 스크립트
│   └── schema.sql        # 데이터베이스 스키마
├── Manifests/            # Kubernetes 매니페스트
├── main.py               # FastAPI 메인 애플리케이션
├── requirements.txt      # Python 패키지 의존성
└── Dockerfile           # Docker 이미지 빌드 파일
```

## 🚀 시작하기

### 로컬 개발 환경 설정

1. 환경 변수 설정 (.env 파일 생성)
```bash
DB_HOST=your-rds-proxy-endpoint
DB_USER=proxy_admin
DB_PASSWORD=test1234
DB_NAME=ott_db
REGION_NAME=ap-northeast-2
```

2. 서버 실행
```bash
./scripts/run_server.sh
```

### 데이터베이스 스키마 생성

Bastion 인스턴스를 통해 데이터베이스 스키마를 생성합니다:

```bash
./scripts/db/deploy_schema.sh
```

또는 직접 Bastion에 접속하여:

```bash
./scripts/db/connect-to-bastion.sh
# Bastion 내부에서
mysql -h y2om-kor-aurora-mysql.cluster-c902seqsaaps.ap-northeast-2.rds.amazonaws.com \
      -u proxy_admin -p'test1234' ott_db < schema.sql
```

### EKS 배포

```bash
./scripts/deploy/deploy-to-eks.sh
```

## 📚 문서

- [API 가이드](docs/API_GUIDE.md)
- [데이터베이스 스키마](docs/DATABASE_SCHEMA.md)
- [배포 가이드](docs/EKS_DEPLOYMENT_GUIDE.md)

## 🗄️ 데이터베이스 스키마

ERD 기반으로 다음 테이블들이 정의되어 있습니다:

- `users` - 사용자 정보
- `contents` - 컨텐츠 정보
- `contents_likes` - 좋아요 정보
- `watch_history` - 시청 기록
- `video_assets` - 영상 파일 정보

자세한 내용은 [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)를 참고하세요.
