"""
LangGraph 상태 정의
전체 자소서 생성 파이프라인에서 사용되는 State 클래스들
"""
from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict, Annotated
from operator import add


# ==========================================
# 공통 데이터 구조
# ==========================================

class CompanyDNA(TypedDict):
    """기업 DNA 정보 (AnalyzerAgent 출력 + DB 저장 포맷)"""
    core_values: List[str]
    ideal_traits: List[str]
    keywords: List[str]
    communication_tone: str
    preferred_experiences: List[str]


class QuestionInfo(TypedDict):
    """자소서 질문 상세 정보 (입력)"""
    id: int
    content: str
    min_length: Optional[int]
    max_length: Optional[int]


class QuestionStrategy(TypedDict):
    """개별 질문에 대한 전략 (StrategistAgent 내부용)"""
    question_index: int
    question: str
    recommended_experiences: List[str]
    key_message: str
    company_value_alignment: str


class MatchingStrategy(TypedDict):
    """매칭 전략 (StrategistAgent 출력)"""
    question_strategies: List[QuestionStrategy]
    key_points: List[str]
    tone_guide: str
    differentiators: List[str]


class GeneratedAnswer(TypedDict):
    """생성된 답변 (WriterAgent 출력)"""
    question_index: int
    content: str
    length: int
    rationale: str # 왜 이렇게 썼는지


class FinalItem(TypedDict):
    """최종 완성된 항목 (OrchestratorAgent 출력)"""
    question: str
    answer: str
    guide_comments: List[str]


class QualityReport(TypedDict):
    """품질 검증 리포트 (OrchestratorAgent 출력)"""
    overall_score: int
    consistency_check: str
    tone_unified: str
    improvements_made: List[str]
    suggestions: List[str]


# ==========================================
# 인재상 추출용
# ==========================================

class ExtractionState(TypedDict):
    """기업 인재상 추출 파이프라인 상태"""
    company_name: str
    company_info: Dict[str, Any]
    job_category: Optional[str]

    search_queries: Annotated[List[str], add]
    search_results: Annotated[List[Dict[str, Any]], add]
    scraping_urls: Annotated[List[str], add]
    scraped_contents: Annotated[List[Dict[str, Any]], add]

    company_dna: Optional[CompanyDNA]

    status: str
    error: Optional[str]


# ==========================================
# 자소서 생성용
# ==========================================

class GenerationState(TypedDict):
    """자소서 생성 파이프라인 상태"""
    user_spec: Dict[str, Any]
    company_dna: Dict[str, Any]   # DB JSON -> TypedDict 변환 필요
    company_info: Dict[str, Any]
    questions: List[QuestionInfo]

    matching_strategy: Optional[MatchingStrategy]

    answers: Annotated[List[GeneratedAnswer], add]

    final_result: Optional[List[FinalItem]]
    quality_report: Optional[QualityReport]

    status: str
    error: Optional[str]