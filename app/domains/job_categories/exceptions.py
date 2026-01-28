"""JobCategory 도메인 Custom Exceptions"""

from fastapi import HTTPException, status


class JobCategoryNotFoundException(HTTPException):
    #직군을 찾을 수 없을 때 발생하는 예외
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다"
        )
