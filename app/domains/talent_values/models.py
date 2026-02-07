from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.shared.database import Base


class CompanyTalentValue(Base):
    __tablename__ = "company_talent_values"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    scope = Column(String(20), nullable=False, default="company")
    job_category_id = Column(Integer, ForeignKey("job_categories.id"), nullable=True)
    values = Column(JSONB, nullable=False)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_company_talent_values_company", "company_id"),
        Index("idx_company_talent_values_job_category", "job_category_id"),
        # PostgreSQL UNIQUE는 NULL을 중복으로 안 보기 때문에 Partial Index 사용
        Index(
            "uq_company_talent_values_company_null_job",
            "company_id",
            unique=True,
            postgresql_where=text("job_category_id IS NULL"),
        ),
        Index(
            "uq_company_talent_values_company_job_not_null",
            "company_id", "job_category_id",
            unique=True,
            postgresql_where=text("job_category_id IS NOT NULL"),
        ),
    )
