"""
LangGraph 상태 정의
전체 자소서 생성 파이프라인에서 사용되는 State 클래스들
"""
from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict, Annotated
from operator import add


class CompanyDNA(TypedDict):
    """기업 DNA 정보 (AnalyzerAgent 출력)"""
    core_values: List[str]  # 핵심 가치
    ideal_traits: List[str]  # 인재 특성
    keywords: List[str]  # 키워드
    communication_tone: str  # 커뮤니케이션 톤
    preferred_experiences: List[str]  # 선호 경험


class QuestionStrategy(TypedDict):
    """개별 질문에 대한 전략"""
    question: str  # 원본 질문
    recommended_experiences: List[str]  # 추천 경험
    key_message: str  # 핵심 메시지
    company_value_alignment: str  # 기업 가치 연결


class MatchingStrategy(TypedDict):
    """매칭 전략 (StrategistAgent 출력)"""
    question_strategies: List[QuestionStrategy]  # 질문별 전략 리스트
    key_points: List[str]  # 핵심 포인트
    experience_to_value_mapping: Dict[str, str]  # 경험-가치 매핑
    tone_guide: str  # 톤 가이드
    differentiators: List[str]  # 차별화 요소


class QualityReport(TypedDict):
    """품질 검증 리포트 (OrchestratorAgent 출력)"""
    overall_score: int  # 전체 점수
    consistency_check: str  # 일관성 체크 결과
    tone_unified: str  # 톤 통일 여부
    improvements_made: List[str]  # 개선 사항
    suggestions: List[str]  # 추가 제안


class CoverLetterState(TypedDict):
    """전체 자소서 생성 파이프라인 State"""

    # ===== 입력 정보 =====
    user_id: int
    company_id: int
    job_category_id: Optional[int]
    questions: List[str]  # 자소서 질문 리스트 (개수 제한 없음)

    # ===== Stage 1: 데이터 수집 (병렬) =====
    # 사용자 및 기업 기본 정보
    user_spec: Optional[Dict[str, Any]]  # 사용자 스펙 정보
    company_info: Optional[Dict[str, Any]]  # 기업 기본 정보 (name, industry, description 등)

    # ResearcherAgent
    search_queries: Annotated[List[str], add]  # 생성된 검색 쿼리들
    search_results: Annotated[List[Dict[str, Any]], add]  # Tavily 검색 결과

    # ScraperAgent
    scraping_urls: Annotated[List[str], add]  # 스크래핑할 URL 목록
    scraped_contents: Annotated[List[Dict[str, Any]], add]  # Firecrawl 스크래핑 결과

    # ===== Stage 2: 분석 및 전략 수립 (순차) =====
    # AnalyzerAgent
    company_dna: Optional[CompanyDNA]  # 추출된 기업 DNA

    # StrategistAgent
    matching_strategy: Optional[MatchingStrategy]  # 기업-사용자 매칭 전략

    # ===== Stage 3: 답변 생성 (병렬) =====
    # WriterAgent (동적 개수의 질문에 대해 병렬 처리)
    answers: List[str]  # 질문별 답변 리스트 (질문 개수만큼)

    # ===== Stage 4: 최종 조합 & 품질 검증 (순차) =====
    # OrchestratorAgent
    final_cover_letter: Optional[str]  # 최종 조합된 자소서
    quality_report: Optional[QualityReport]  # 품질 검증 리포트

    # ===== 메타데이터 =====
    generation_metadata: Dict[str, Any]  # 생성 과정 메타데이터 (모델명, 토큰 수, 실행 시간 등)
    status: str  # 상태: pending, processing, completed, failed
    error: Optional[str]  # 에러 메시지