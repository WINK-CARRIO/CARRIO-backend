class CompanyNotFoundError(Exception):
    """기업을 찾을 수 없음 (404)"""
    pass


class CompanyDuplicateError(Exception):
    """기업명 중복 (409)"""
    pass
