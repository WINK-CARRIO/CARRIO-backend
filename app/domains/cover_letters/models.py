from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.shared.database import Base


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_spec_id = Column(Integer, ForeignKey("user_specs.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    job_category_id = Column(Integer, ForeignKey("job_categories.id", ondelete="RESTRICT"), nullable=True)
    # 질문-답변 항목들 (JSONB 배열)
    # [{ "question": { "content": "...", "min_length": 500, "max_length": 700 },
    #    "answer": { "content": "...", "length": 650, "guide_comments": [...] } }, ...]
    items = Column(JSONB, nullable=False)
    # question = Column(Text, nullable=False)
    # content = Column(Text)
    status = Column(String(50), default="pending")
    generation_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    user_spec = relationship("UserSpec")
    company = relationship("Company")
    job_category = relationship("JobCategory")

    # 인덱스
    __table_args__ = (
        Index("idx_cover_letters_user", "user_id"),
        Index("idx_cover_letters_company", "company_id"),
        Index("idx_cover_letters_status", "status"),
    )