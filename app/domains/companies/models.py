from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.shared.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    industry = Column(String(100))
    description = Column(Text)
    logo_url = Column(String(500))
    website_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
