from typing import List

from sqlalchemy.orm import Session
from .models import JobCategory
from .schemas import JobCategoryCreate, JobCategoryUpdate
from .exceptions import JobCategoryNotFoundError, JobCategoryDuplicateError


def create_job_category(db: Session, data: JobCategoryCreate) -> JobCategory:
    # 직군명 중복 체크
    existing = db.query(JobCategory).filter(JobCategory.name == data.name).first()
    if existing:
        raise JobCategoryDuplicateError()

    job_category = JobCategory(
        name=data.name,
        description=data.description,
    )
    db.add(job_category)
    db.commit()
    db.refresh(job_category)
    return job_category


def get_job_categories(db: Session) -> List[JobCategory]:
    return db.query(JobCategory).order_by(JobCategory.name.asc()).all()


def update_job_category(db: Session, job_category_id: int, data: JobCategoryUpdate) -> JobCategory:
    job_category = db.query(JobCategory).filter(JobCategory.id == job_category_id).first()
    if not job_category:
        raise JobCategoryNotFoundError()

    # 직군명 변경 시 중복 체크
    if data.name and data.name != job_category.name:
        existing = db.query(JobCategory).filter(JobCategory.name == data.name).first()
        if existing:
            raise JobCategoryDuplicateError()

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job_category, key, value)

    db.commit()
    db.refresh(job_category)
    return job_category


def delete_job_category(db: Session, job_category_id: int) -> None:
    job_category = db.query(JobCategory).filter(JobCategory.id == job_category_id).first()
    if not job_category:
        raise JobCategoryNotFoundError()

    db.delete(job_category)
    db.commit()
