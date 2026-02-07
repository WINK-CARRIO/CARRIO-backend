from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from datetime import datetime


# --- 요청 스키마 ---

class TalentValueUpdate(BaseModel):
    """전사 인재상 수정 요청"""
    keywords: List[str]
    description: str
    details: List[str]


class JobSpecificValue(BaseModel):
    """직무별 인재상 데이터"""
    keywords: List[str]
    description: str
    details: List[str]
    technical_requirements: Optional[List[str]] = None


class JobTalentValueUpdate(BaseModel):
    """직무 인재상 수정 요청"""
    job_specific: JobSpecificValue


# --- 응답 스키마 ---

class CompanyTalentValueResponse(BaseModel):
    """전사 인재상 조회 응답"""
    id: int
    company_id: int
    company_name: str
    talent_values: Dict[str, Any]
    extracted_at: datetime


class JobTalentValueResponse(BaseModel):
    """직무별 인재상 조회 응답"""
    id: int
    company_id: int
    company_name: str
    job_category_id: int
    job_category_name: str
    talent_values: Dict[str, Any]
    extracted_at: datetime


class AdminTalentValueResponse(BaseModel):
    """Admin 전사 인재상 수정/삭제 응답"""
    id: int
    company_id: int
    talent_values: Dict[str, Any]
    extracted_at: datetime


class AdminJobTalentValueResponse(BaseModel):
    """Admin 직무 인재상 수정/삭제 응답"""
    id: int
    company_id: int
    job_category_id: int
    talent_values: Dict[str, Any]
    extracted_at: datetime
