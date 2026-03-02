"""User 도메인 Custom Exceptions"""

from fastapi import HTTPException, status


class UserSpecNotFoundException(HTTPException):
    #사용자 스펙을 찾을 수 없을 때 발생하는 예외
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스펙을 찾을 수 없습니다"
        )


class UserSpecAlreadyExistsException(HTTPException):
    #이미 사용자 스펙이 존재할 때 발생하는 예외
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 스펙이 존재합니다"
        )
