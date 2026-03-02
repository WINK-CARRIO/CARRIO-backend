# Database 패키지
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# [의도] config.py의 Settings에서 DATABASE_URL을 가져옴 (.env 파일 자동 로드)
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


#
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()