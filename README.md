# CARRIO Backend

> 기업 DNA 기반 AI 자소서 생성 서비스

---

## 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/WINK-CARRIO/CARRIO-backend.git
cd CARRIO-backend
```

### 2. 가상환경 설정
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.example .env
```

**`.env` 파일을 열어서 필수 값 수정:**
```bash
# 필수! OpenAI API 키 발급
# https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-실제발급받은키로변경

# 선택: 카카오 로그인 사용 시
# https://developers.kakao.com
KAKAO_CLIENT_ID=실제REST_API_키
KAKAO_CLIENT_SECRET=실제시크릿키

# JWT 시크릿 키 변경 (32자 이상)
SECRET_KEY=랜덤한-32자-이상의-시크릿-키-생성
```

**API 키 발급:**
- **OpenAI**: https://platform.openai.com/api-keys
- **Kakao**: https://developers.kakao.com
- **Anthropic** (선택): https://console.anthropic.com

### 5. 데이터베이스 실행
```bash
# PostgreSQL + pgvector 실행
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f postgres
```

### 6. 데이터베이스 마이그레이션
```bash
# Alembic으로 DB 스키마 생성
alembic upgrade head
```

> **참고**: Alembic은 Git처럼 DB 스키마를 버전 관리합니다.
> 자세한 사용법은 [ALEMBIC_GUIDE.md](./ALEMBIC_GUIDE.md)를 참고하세요.

### 7. 서버 실행
```bash
# venv 변경 감지 제외하고 실행 (권장)
uvicorn app.main:app --reload --reload-exclude 'venv/*'

# 또는 일반 실행
uvicorn app.main:app --reload
```

> **참고**: DB 테이블은 Alembic 마이그레이션으로 관리됩니다.
> pgvector 확장은 Docker 이미지에 포함되어 있습니다.

**서버 접속:**
- Health Check: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 프로젝트 구조

```
CARRIO-backend/
├── app/
│   ├── main.py              # FastAPI 진입점
│   ├── config.py            # 환경 설정
│   ├── shared/              # 공통 모듈
│   │   └── database/        # DB 연결 설정
│   └── domains/             # 도메인별 폴더
│       ├── auth/            # 인증 (로그인, 카카오 OAuth)
│       ├── users/           # 사용자 관리
│       ├── companies/       # 기업 정보
│       └── job_categories/  # 직무 카테고리
├── alembic/                 # DB 마이그레이션
│   └── versions/            # 마이그레이션 파일들
├── docker-compose.yml       # PostgreSQL 설정
├── requirements.txt
├── .env.example
└── README.md
```

---

## 개발 환경

### 필수 요구사항
- Python 3.9+
- Docker Desktop
- PostgreSQL (Docker로 실행)
- OpenAI API Key

### 데이터베이스 GUI 툴 (선택)

**TablePlus (Mac 추천):**
```bash
brew install --cask tableplus
```

**DBeaver (Windows/Linux 추천):**
```bash
brew install --cask dbeaver-community
```

**연결 정보:**
- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password: `postgres123`
- Database: `CARRIO`

---

## Kakao OAuth 설정

### Redirect URI

카카오 개발자 콘솔에 아래 Redirect URI를 등록해야 합니다.

- Local:
    - http://localhost:8000/api/v1/auth/kakao/callback

- Production:
    - https://api.example.com/api/v1/auth/kakao/callback

Redirect URI는 정확히 일치해야 하며,
프론트엔드 로그인 요청 시에도 동일한 URI를 사용해야 합니다.
