"""
자소서 생성 관련 커스텀 예외
"""


class CoverLetterNotFoundError(Exception):
    """자소서를 찾을 수 없음 (404)"""
    pass


class CoverLetterGenerationError(Exception):
    """자소서 생성 실패 (500)"""
    pass


class CompanyResearchError(Exception):
    """기업 리서치 실패 (500)"""
    pass


class UserSpecNotFoundError(Exception):
    """사용자 스펙을 찾을 수 없음 (404)"""
    pass


class InvalidRequestError(Exception):
    """잘못된 요청 (400)"""
    pass


class CompanyDNAExtractionError(Exception):
    """기업 DNA 추출 실패 (500)"""
    pass


class StrategyPlanningError(Exception):
    """전략 수립 실패 (500)"""
    pass


class UserSpecAnalysisError(Exception):
    """사용자 스펙 분석 실패 (500)"""
    pass