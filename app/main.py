from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel
from app.domains.users import router as users_routes
from app.domains.auth import router as auth_routes
from app.domains.companies import router as companies_routes
from app.domains.job_categories import router as job_categories_routes
from app.domains.talent_values import router as talent_values_routes
from app.domains.cover_letters import router as cover_letters_routes
from app.domains.auth.exception_handlers import register_auth_exception_handlers
from app.shared.database import Base, engine

# 테이블 생성은 Alembic 마이그레이션으로 관리합니다
# 새 테이블 추가 시: alembic revision --autogenerate -m "Add new table"
# DB에 적용: alembic upgrade head
# Base.metadata.create_all(bind=engine)  # ← Alembic 사용으로 더 이상 필요 없음

# 간단한 응답 스키마 (임시)
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime

app = FastAPI(
    title="자소서 에이전트 API",
    description="기업 DNA 기반 자소서 생성 및 분석 서비스",
    version="0.1.0"
)

# CORS 설정 (프론트엔드 개발용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://carrioclient.vercel.app","https://carrio.junhwan.me"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_auth_exception_handlers(app)

@app.get("/", response_model=HealthCheck)
def root():
    """헬스 체크"""
    return HealthCheck(
        status="ok",
        timestamp=datetime.now()
    )

@app.get("/health", response_model=HealthCheck)
def health_check():
    """헬스 체크"""
    return HealthCheck(
        status="ok",
        timestamp=datetime.now()
    )


# TODO: 각 도메인 라우터 등록 (팀원들이 구현 후 추가)
# from app.domains.users import routes as users_routes
# from app.domains.companies import routes as companies_routes
# from app.domains.cover_letters import routes as cover_letters_routes
# from app.domains.agents import routes as agents_routes

app.include_router(users_routes.router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(companies_routes.router, prefix="/api/v1")
app.include_router(job_categories_routes.router, prefix="/api/v1")
app.include_router(cover_letters_routes.router, prefix="/api/v1")
app.include_router(talent_values_routes.router, prefix="/api/v1")
