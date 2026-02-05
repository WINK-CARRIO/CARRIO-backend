from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.shared.database import get_db
from app.domains.auth.dependencies import get_current_user, get_admin_user
from app.domains.users.models import User
from .schemas import JobCategoryCreate, JobCategoryUpdate, JobCategoryResponse
from .service import create_job_category, get_job_categories, update_job_category, delete_job_category
from .exceptions import JobCategoryNotFoundError, JobCategoryDuplicateError

router = APIRouter(tags=["Job Categories"])


@router.get("/job-categories", response_model=List[JobCategoryResponse])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """직군 목록 조회 (이름순 정렬)"""
    return get_job_categories(db)


@router.post("/admin/job-categories", response_model=JobCategoryResponse, status_code=status.HTTP_201_CREATED)
def create(
    body: JobCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """직군 생성 (Admin 전용)"""
    try:
        return create_job_category(db, body)
    except JobCategoryDuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 직군명입니다",
        )


@router.put("/admin/job-categories/{job_category_id}", response_model=JobCategoryResponse)
def update(
    job_category_id: int,
    body: JobCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """직군 수정 (Admin 전용)"""
    try:
        return update_job_category(db, job_category_id, body)
    except JobCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다",
        )
    except JobCategoryDuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 직군명입니다",
        )


@router.delete("/admin/job-categories/{job_category_id}")
def delete(
    job_category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """직군 삭제 (Admin 전용)"""
    try:
        delete_job_category(db, job_category_id)
        return {"message": "직군이 삭제되었습니다"}
    except JobCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다",
        )
