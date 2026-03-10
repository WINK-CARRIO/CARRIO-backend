from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class JobCategoryResponse(BaseModel):
    """직군 카테고리 응답"""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobCategoryListResponse(BaseModel):
    """직군 목록 응답 래핑"""
    job_categories: List[JobCategoryResponse]


class JobCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class JobCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
