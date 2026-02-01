"""CoverLetter 도메인 Custom Exceptions"""

from fastapi import HTTPException, status


class CoverLetterNotFoundException(HTTPException):
    """자소서를 찾을 수 없을 때 발생하는 예외"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="자소서를 찾을 수 없습니다"
        )


class CoverLetterGenerationFailedException(HTTPException):
    """자소서 생성 실패 시 발생하는 예외"""
    def __init__(self, message: str = "자소서 생성에 실패했습니다"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )


class CoverLetterForbiddenException(HTTPException):
    """자소서 접근 권한이 없을 때 발생하는 예외"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 자소서에 대한 접근 권한이 없습니다"
        )


class InvalidQuestionException(HTTPException):
    """유효하지 않은 질문일 때 발생하는 예외"""
    def __init__(self, message: str = "유효하지 않은 질문입니다"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )


class CompanyNotFoundException(HTTPException):
    """기업을 찾을 수 없을 때 발생하는 예외"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다"
        )
