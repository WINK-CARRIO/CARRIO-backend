class JobCategoryNotFoundError(Exception):
    """직군을 찾을 수 없음 (404)"""
    pass


class JobCategoryDuplicateError(Exception):
    """직군명 중복 (409)"""
    pass
