class JobCategoryNotFoundError(Exception):
    """직군을 찾을 수 없음 (404)"""
    pass


class JobCategoryDuplicateError(Exception):
    """직군명 중복 (409)"""
    pass


class JobCategoryInUseError(Exception):
    """직군이 사용 중이라 삭제 불가 (409)"""
    pass
