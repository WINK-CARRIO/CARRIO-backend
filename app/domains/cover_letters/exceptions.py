class CoverLetterNotFoundException(Exception):
    """자소서를 찾을 수 없음 (404)"""
    pass


class CoverLetterGenerationFailedException(Exception):
    """자소서 생성 실패 (500)"""
    pass


class CoverLetterForbiddenException(Exception):
    """자소서 접근 권한 없음 (403)"""
    pass


class InvalidQuestionException(Exception):
    """유효하지 않은 질문 데이터 (400)"""
    pass


class CompanyNotFoundException(Exception):
    """기업을 찾을 수 없음 (404)"""
    pass
