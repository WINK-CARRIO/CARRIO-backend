"""
자소서 생성 서비스 및 에이전트 관련 커스텀 예외 정의
"""

# ===== Base Exceptions =====

class BaseServiceError(Exception):
    """서비스 로직 관련 기본 예외"""
    pass


class BaseAgentError(Exception):
    """AI 에이전트 수행 중 발생하는 기본 예외 (Graph 중단용)"""
    pass


# ===== Agent Layer Exceptions (LangGraph Node용) =====

class SearchError(BaseAgentError):
    """Tavily 검색 실패 또는 API 키 누락"""
    pass


class ScrapingError(BaseAgentError):
    """Firecrawl 스크래핑 실패 또는 API 키 누락"""
    pass


class CompanyResearchError(BaseAgentError):
    """기업 정보 수집 단계 포괄적 실패"""
    pass


class CompanyDNAExtractionError(BaseAgentError):
    """기업 DNA 추출 실패 (AnalyzerAgent)"""
    pass


class StrategyPlanningError(BaseAgentError):
    """자소서 전략 수립 실패 (StrategistAgent)"""
    pass


class CoverLetterGenerationError(BaseAgentError):
    """자소서 답변 작성 또는 최종 조합 실패 (Writer/Orchestrator Agent)"""
    pass