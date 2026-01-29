from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.shared.database import get_db
from app.domains.auth.dependencies import get_current_user
from app.domains.users.models import User
from .models import JobCategory
from .schemas import JobCategoryResponse

router = APIRouter(prefix="/job-categories", tags=["Job Categories"])


@router.get("", response_model=List[JobCategoryResponse])
def get_job_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    직군 목록 조회
    
    - 모든 로그인 사용자 접근 가능
    - 직군 목록을 반환합니다
    """
    job_categories = db.query(JobCategory).all()
    return job_categories
