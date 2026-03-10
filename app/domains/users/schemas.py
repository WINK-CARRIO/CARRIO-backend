from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    oauth_provider: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== UserSpec 관련 스키마 ==========

class Education(BaseModel):
    """학력 정보"""
    school: Optional[str] = None
    major: Optional[str] = None
    admission_year: Optional[int] = None  # 입학 년도
    grad_year: Optional[int] = None       # 졸업 년도
    gpa: Optional[float] = None
    gpa_scale: Optional[float] = None  # 만점 기준 (4.5, 4.3, 4.0 등)

    model_config = ConfigDict(extra="allow")  # 추가 필드 허용


class Certification(BaseModel):
    """자격증 정보"""
    name: str  # 필수: 자격증명
    acquired_date: Optional[str] = None  # 취득 날짜 (YYYY-MM 또는 YYYY)
    expiry_date: Optional[str] = None    # 유효 기간 만료일 (YYYY-MM 또는 YYYY)

    model_config = ConfigDict(extra="allow")  # 추가 필드 허용


class StructuredData(BaseModel):
    """정형 데이터 (구조화된 검증)"""
    education: Optional[Education] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[Certification]] = None  # 자격증 객체 리스트
    awards: Optional[List[str]] = None
    language_scores: Optional[List[Dict[str, Any]]] = None  # 토익, 토플 등

    model_config = ConfigDict(extra="allow")  # 추가 필드 허용


class Experience(BaseModel):
    """경험 정보 (최소 필드만 정의, 나머지는 자유롭게 추가 가능)"""
    type: Optional[str] = None  # 프론트엔드에서 자유롭게 정의
    title: str  # 필수
    description: str  # 필수
    period: Optional[str] = None

    model_config = ConfigDict(extra="allow")  # role, achievements 등 추가 필드 허용


class UserSpecCreate(BaseModel):
    """스펙 생성 요청"""
    job_category_id: Optional[int] = None
    structured_data: Optional[StructuredData] = None
    free_experiences: Optional[List[Experience]] = None


class UserSpecUpdate(BaseModel):
    """스펙 수정 요청 (모든 필드 Optional)"""
    job_category_id: Optional[int] = None
    structured_data: Optional[StructuredData] = None
    free_experiences: Optional[List[Experience]] = None


class UserSpecResponse(BaseModel):
    """스펙 응답"""
    id: int
    user_id: int
    job_category_id: Optional[int] = None
    structured_data: Optional[Dict[str, Any]] = None
    free_experiences: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True