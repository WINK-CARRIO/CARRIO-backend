# CARRIO Backend - FastAPI Server

기업 DNA 기반 자소서 생성 및 분석 서비스 백엔드 서버

## 아키텍처 개요 (Modular Monolith)

```
CARRIO-backend/
├── app/
│   ├── domains/             # 도메인별 모듈 분리
│   │   ├── auth/            # 인증 (Kakao, JWT)
│   │   ├── users/           # 사용자 관리
│   │   ├── companies/       # 기업 정보
│   │   └── job_categories/  # 직군 관리
│   │
│   ├── shared/              # 공용 모듈
│   │   └── database/        # DB 연결 및 Base 모델
│   │
│   └── main.py              # FastAPI 앱 진입점
```

**특징**:
- 도메인 주도 설계(DDD)를 지향하는 모듈형 구조
- Pydantic v2와 SQLAlchemy 2.0 사용
- Alembic을 이용한 마이그레이션 관리

## 기술 스택

| 분류 | 기술 |
|------|------|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL (psycopg2) |
| ORM | SQLAlchemy 2.0 |
| Migration | Alembic |
| Auth | JWT, Kakao OAuth |
| AI/LLM | OpenAI, LangChain, LangGraph |
| Validation | Pydantic v2 |

## 프로젝트 구조

```
CARRIO-backend/
├── main.py                     # (X) app/main.py 사용
├── app/
│   ├── config.py               # 환경 설정 (pydantic-settings)
│   ├── main.py                 # 앱 진입점, 미들웨어, 라우터 등록
│   │
│   ├── domains/                # 기능별 도메인 (각 폴더에 router, schemas, models, service 포함 권장)
│   │   ├── auth/               # kakao.py, router.py 등
│   │   ├── companies/
│   │   ├── job_categories/
│   │   └── users/
│   │
│   └── shared/
│       └── database/           # __init__.py (engine, SessionLocal, Base)
│
├── alembic/                    # 마이그레이션 스크립트
├── alembic.ini                 # 마이그레이션 설정
├── requirements.txt            # 의존성 목록
└── .env                        # 환경 변수 (보안 주의)
```

## 환경 변수 (.env)

`app/config.py` 참조

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# OpenAI
OPENAI_API_KEY=sk-...

# Kakao OAuth
KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=

# JWT
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## 명령어 가이드

### 개발 서버 실행
```bash
# 가상환경 활성화 (필요시)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (Hot Reload)
uvicorn app.main:app --reload
```

### 데이터베이스 마이그레이션 (Alembic)
```bash
# 새 마이그레이션 파일 생성 (모델 변경 후)
alembic revision --autogenerate -m "메시지"

# DB에 적용
alembic upgrade head
```

## API 엔드포인트 규칙
Base path: `/api/v1`

| 도메인 | 경로 | 주요 기능 |
|--------|------|------|
| Auth | `/api/v1/auth/kakao` | 카카오 로그인/콜백 |
| Users | `/api/v1/users` | 사용자 조회/수정 |
| Companies | `/api/v1/companies` | 기업 CRUD |
| Job Categories | `/api/v1/job-categories` | 직군 목록 조회 (인증 사용자) |
| Job Categories | `/api/v1/admin/job-categories` | 직군 생성/수정/삭제 (Admin) |

## 개발 규칙 (Conventions)

### 1. 코드 스타일 & 구조
- **도메인 격리**: 각 도메인(`app/domains/{name}`) 내에서 독립적으로 기능 구현.
- **Type Hint Validaton**: Pydantic 스키마를 사용하여 요청/응답 타입을 엄격히 정의.
- **Dependency Injection**: DB 세션(`get_db`)과 현재 사용자(`current_user`)는 FastAPI `Depends`로 주입.

### 2. 사용자(User) 정의 규칙 (중요) 🚨
- **Git 커밋**: `[TYPE] 설명` 형식 (예: `[FEAT] 직군 생성 API 구현`).
- **주석**: "무엇을" 했는지보다 "왜" 했는지 의도를 설명.
  - `# 사용자가 0명일 때 예외 처리` (O)
  - `"""사용자가 없는 경우 에러를 발생시킵니다."""` (X - 장황함 금지)

### 3. 세션 관리 가이드 (Session Rules)
- **Daily Wrap-up**: 작업 종료 시 "기록해줘" 요청으로 `Lessons Learned` 업데이트.
- **Context**: 이 파일을 항상 최신 상태로 유지하여 다음 대화에서도 문맥이 이어지도록 함.

---

## Lessons Learned (배운 점)
*여기에 프로젝트를 진행하며 배운 중요한 기술적 교훈이나 트러블슈팅 경험을 누적합니다.*

- 예외 클래스 네이밍은 도메인간 일관성 유지 필요 (`~NotFoundError`, `~DuplicateError` 패턴) - 2026.02.05
- Service 레이어에서 커스텀 예외를 raise하고, Router에서 try-except로 HTTPException 변환하는 패턴이 깔끔함 - 2026.02.05
- 다른 도메인에서 예외 클래스를 import할 때, 클래스명 변경 시 의존하는 모든 파일 수정 필요 (users/service.py → job_categories/exceptions.py) - 2026.02.05

## Anti-Patterns (하지 말아야 할 것)
*같은 실수를 반복하지 않기 위해 기록합니다.*

- Pydantic 모델에서 ORM 객체를 반환할 때 `from_attributes=True` (구 `orm_mode`) 설정을 누락하지 말 것
- 순환 참조를 피하기 위해 Pydantic 스키마와 SQLAlchemy 모델 파일은 철저히 분리할 것
- Router에서 prefix와 개별 경로에 중복 경로 지정하지 말 것 (예: `APIRouter(prefix="/job-categories")` + `@router.post("/admin/job-categories")` → 경로 꼬임)

## 향후 개발 참고사항 (Next Steps)
- [x] Job Category CRUD 완료 (2026.02.05)
- [ ] Cover Letter (자소서) 도메인 설계 및 구현
- [ ] 카카오 로그인 연동 테스트 완료
