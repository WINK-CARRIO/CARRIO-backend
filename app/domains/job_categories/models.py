from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.shared.database import Base


class JobCategory(Base):
    """직군 카테고리 모델"""
    __tablename__ = "job_categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
