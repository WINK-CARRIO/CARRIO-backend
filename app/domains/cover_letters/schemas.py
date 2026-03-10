from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ========== 요청 스키마 ==========

class QuestionInput(BaseModel):
    """질문 입력"""
    content: str = Field(..., description="질문 내용")
    min_length: int = Field(default=500, description="최소 글자 수")
    max_length: int = Field(default=700, description="최대 글자 수")


class CoverLetterCreateRequest(BaseModel):
    """자소서 생성 요청"""
    company_id: int = Field(..., description="기업 ID")
    job_category_id: Optional[int] = Field(None, description="직군 카테고리 ID")
    questions: List[QuestionInput] = Field(..., min_length=1, description="질문 목록")


class AnswerUpdateInput(BaseModel):
    """답변 수정 입력"""
    content: str = Field(..., description="수정된 답변 내용")


class CoverLetterItemUpdateInput(BaseModel):
    """자소서 항목 수정 입력"""
    question: QuestionInput = Field(..., description="질문 (매칭용)")
    answer: AnswerUpdateInput = Field(..., description="수정된 답변")


class CoverLetterUpdateRequest(BaseModel):
    """자소서 수정 요청"""
    items: List[CoverLetterItemUpdateInput] = Field(..., min_length=1, description="수정된 항목 목록")


# ========== 응답 스키마 ==========

class QuestionResponse(BaseModel):
    """질문 응답"""
    content: str
    min_length: int
    max_length: int


class AnswerResponse(BaseModel):
    """답변 응답"""
    content: str
    length: int
    guide_comments: List[str] = []


class CoverLetterItemResponse(BaseModel):
    """자소서 항목 응답"""
    question: QuestionResponse
    answer: AnswerResponse


class CoverLetterResponse(BaseModel):
    """자소서 생성 응답"""
    id: int
    user_id: int
    company_id: int
    company_name: str
    job_category_id: Optional[int]
    job_category_name: Optional[str]
    status: str
    created_at: datetime
    items: List[CoverLetterItemResponse]

    class Config:
        from_attributes = True


class CoverLetterListItem(BaseModel):
    """자소서 목록 아이템"""
    id: int
    company_name: str
    company_logo_url: Optional[str] = None
    job_category_name: Optional[str]
    overall_score: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CoverLetterListResponse(BaseModel):
    """자소서 목록 응답"""
    total: int
    page: int
    limit: int
    data: List[CoverLetterListItem]


class CoverLetterDetailResponse(BaseModel):
    """자소서 상세 조회 응답"""
    cover_letter: CoverLetterResponse
    matching_analysis: Optional[Dict[str, Any]] = None


class CoverLetterDeleteResponse(BaseModel):
    """자소서 삭제 응답"""
    message: str = "자소서가 삭제되었습니다"