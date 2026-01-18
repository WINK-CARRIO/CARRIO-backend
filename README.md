# 자소서 에이전트 백엔드

## 🚀 실행 방법

### 1. 가상환경 설정
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
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

**API 키 발급 방법:**
- **OpenAI**: https://platform.openai.com/api-keys
- **Kakao**: https://developers.kakao.com → 애플리케이션 추가
- **Anthropic (선택)**: https://console.anthropic.com
- **Tavily (선택)**: https://tavily.com

### 4. 데이터베이스 실행 (Docker Compose)
```bash
# PostgreSQL + pgvector 실행
docker-compose up -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f postgres
```

### 5. 스키마 적용 (최초 1회)
```bash
# DB 컨테이너 안에서 실행
docker-compose exec postgres psql -U postgres -d coverletter -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 스키마 적용
docker-compose exec -T postgres psql -U postgres -d coverletter < ../docs/database_schema.sql
```

### 5. 서버 실행
```bash
uvicorn app.main:app --reload
```

서버 실행 후: http://localhost:8000/docs (Swagger UI)

## 👥 팀원 세팅 가이드

### 첫 세팅 (클론 후)

```bash
# 1. 저장소 클론
git clone <repo-url>
cd backend

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경변수 복사 및 수정
cp .env.example .env
# .env 파일 열어서 OPENAI_API_KEY 등 수정

# 5. Docker 실행
docker-compose up -d

# 6. 데이터베이스 확인
docker-compose exec postgres psql -U postgres -c "\l"

# 7. 서버 실행
uvicorn app.main:app --reload

# 8. 테스트
curl http://localhost:8000/health
```

### GUI 툴 설치 (선택)

**TablePlus (Mac 추천)**:
```bash
brew install --cask tableplus
```
연결 정보:
- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password: `postgres123`
- Database: `coverletter`

**DBeaver (Windows/Linux 추천)**:
```bash
brew install --cask dbeaver-community
```

---

## 📞 도움말

문제 발생 시:
1. 위 트러블슈팅 섹션 확인
2. `docker-compose logs` 로그 확인
3. 팀 채팅방에 에러 메시지 공유

---

## 📂 프로젝트 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 환경 설정
│   ├── database.py          # DB 연결
│   ├── shared/              # 공통 모듈
│   │   ├── schemas.py       # 공통 스키마 (CurrentUser)
│   │   ├── auth.py          # 인증 (Mock → 실제 구현)
│   │   ├── database/        # pgvector 검색
│   │   ├── oauth/           # 카카오 OAuth
│   │   └── llm/             # OpenAI 클라이언트
│   └── domains/             # 도메인별 폴더
│       ├── users/           # 사용자 관리
│       ├── companies/       # 기업 정보 관리
│       ├── cover_letters/   # 자소서 생성
│       └── agents/          # AI 에이전트
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔑 환경 변수 (.env)

```env
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/coverletter
OPENAI_API_KEY=sk-...
KAKAO_CLIENT_ID=...
KAKAO_CLIENT_SECRET=...
SECRET_KEY=your-secret-key-for-jwt
```

---

## 📝 API 문서

서버 실행 후:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
