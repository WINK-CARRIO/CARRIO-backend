from sqlalchemy.orm import Session

from .models import User, UserSpec
from .schemas import UserSpecCreate, UserSpecUpdate
from .exceptions import UserSpecNotFoundException, UserSpecAlreadyExistsException
from app.domains.job_categories.models import JobCategory
from app.domains.job_categories.exceptions import JobCategoryNotFoundError


def _validate_job_category(db: Session, category_id: int) -> None:
    #직군 유효성 검증
    job_category = db.query(JobCategory).filter(
        JobCategory.id == category_id
    ).first()
    if not job_category:
        raise JobCategoryNotFoundError()


def create_user_spec(
    db: Session,
    user: User,
    spec_data: UserSpecCreate
) -> UserSpec:
    #이미 스펙이 존재하는지 확인 (1:1 관계)
    existing_spec = db.query(UserSpec).filter(UserSpec.user_id == user.id).first()
    if existing_spec:
        raise UserSpecAlreadyExistsException()
    
    if spec_data.job_category_id is not None:
        _validate_job_category(db, spec_data.job_category_id)
    
    #스펙 생성
    new_spec = UserSpec(
        user_id=user.id,
        job_category_id=spec_data.job_category_id,
        structured_data=spec_data.structured_data.model_dump() if spec_data.structured_data else None,
        free_experiences=[exp.model_dump() for exp in spec_data.free_experiences] if spec_data.free_experiences else None
    )
    
    db.add(new_spec)
    db.commit()
    db.refresh(new_spec)
    
    return new_spec


def get_user_spec(db: Session, user: User) -> UserSpec:
    spec = db.query(UserSpec).filter(UserSpec.user_id == user.id).first()
    if not spec:
        raise UserSpecNotFoundException()
    return spec


def update_user_spec(
    db: Session,
    user: User,
    spec_data: UserSpecUpdate
) -> UserSpec:
    spec = db.query(UserSpec).filter(UserSpec.user_id == user.id).first()
    if not spec:
        raise UserSpecNotFoundException()
    
    if spec_data.job_category_id is not None:
        _validate_job_category(db, spec_data.job_category_id)
        spec.job_category_id = spec_data.job_category_id
    
    #structured_data 업데이트 (제공된 경우만)
    if spec_data.structured_data is not None:
        spec.structured_data = spec_data.structured_data.model_dump()
    
    #free_experiences 업데이트 (제공된 경우만)
    if spec_data.free_experiences is not None:
        spec.free_experiences = [exp.model_dump() for exp in spec_data.free_experiences]
    
    db.commit()
    db.refresh(spec)
    
    return spec


def delete_user_spec(db: Session, user: User) -> None:
    spec = db.query(UserSpec).filter(UserSpec.user_id == user.id).first()
    if not spec:
        raise UserSpecNotFoundException()
    
    db.delete(spec)
    db.commit()
