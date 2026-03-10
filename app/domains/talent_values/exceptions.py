class TalentValueNotFoundError(Exception):
    """인재상을 찾을 수 없음 (404)"""
    pass


class TalentValueDuplicateError(Exception):
    """인재상 중복 (409)"""
    pass
