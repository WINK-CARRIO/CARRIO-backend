from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from .models import User, UserSpec
from .schemas import UserSpecCreate, UserSpecUpdate
from app.domains.companies.models import JobCategory


def create_user_spec(
    db: Session,
    user_id: int,
    spec_data: UserSpecCreate
) -> UserSpec:
    """
    사용자 스펙 생성
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        spec_data: 스펙 생성 데이터
    
    Returns:
        생성된 UserSpec 객체
    
    Raises:
        HTTPException 404: 사용자가 존재하지 않는 경우
        HTTPException 404: job_category_id가 유효하지 않은 경우
        HTTPException 409: 이미 스펙이 존재하는 경우
    """
    # 사용자 존재 확인
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 이미 스펙이 존재하는지 확인 (1:1 관계)
    existing_spec = db.query(UserSpec).filter(UserSpec.user_id == user_id).first()
    if existing_spec:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 스펙이 존재합니다"
        )
    
    # job_category_id 유효성 검증
    if spec_data.job_category_id is not None:
        job_category = db.query(JobCategory).filter(
            JobCategory.id == spec_data.job_category_id
        ).first()
        if not job_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="직군을 찾을 수 없습니다"
            )
    
    # 스펙 생성
    new_spec = UserSpec(
        user_id=user_id,
        job_category_id=spec_data.job_category_id,
        structured_data=spec_data.structured_data.model_dump() if spec_data.structured_data else None,
        free_experiences=[exp.model_dump() for exp in spec_data.free_experiences] if spec_data.free_experiences else None
    )
    
    db.add(new_spec)
    db.commit()
    db.refresh(new_spec)
    
    return new_spec


def get_user_spec(db: Session, user_id: int) -> UserSpec:
    """
    사용자 스펙 조회
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
    
    Returns:
        UserSpec 객체
    
    Raises:
        HTTPException 404: 스펙이 존재하지 않는 경우
    """
    spec = db.query(UserSpec).filter(UserSpec.user_id == user_id).first()
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스펙을 찾을 수 없습니다"
        )
    return spec


def update_user_spec(
    db: Session,
    user_id: int,
    spec_data: UserSpecUpdate
) -> UserSpec:
    """
    사용자 스펙 수정 (부분 업데이트)
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        spec_data: 스펙 수정 데이터
    
    Returns:
        수정된 UserSpec 객체
    
    Raises:
        HTTPException 404: 스펙이 존재하지 않는 경우
        HTTPException 404: job_category_id가 유효하지 않은 경우
    """
    spec = db.query(UserSpec).filter(UserSpec.user_id == user_id).first()
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스펙을 찾을 수 없습니다"
        )
    
    # job_category_id 유효성 검증
    if spec_data.job_category_id is not None:
        job_category = db.query(JobCategory).filter(
            JobCategory.id == spec_data.job_category_id
        ).first()
        if not job_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="직군을 찾을 수 없습니다"
            )
        spec.job_category_id = spec_data.job_category_id
    
    # structured_data 업데이트 (제공된 경우만)
    if spec_data.structured_data is not None:
        spec.structured_data = spec_data.structured_data.model_dump()
    
    # free_experiences 업데이트 (제공된 경우만)
    if spec_data.free_experiences is not None:
        spec.free_experiences = [exp.model_dump() for exp in spec_data.free_experiences]
    
    db.commit()
    db.refresh(spec)
    
    return spec


def delete_user_spec(db: Session, user_id: int) -> None:
    """
    사용자 스펙 삭제
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
    
    Raises:
        HTTPException 404: 스펙이 존재하지 않는 경우
    """
    spec = db.query(UserSpec).filter(UserSpec.user_id == user_id).first()
    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스펙을 찾을 수 없습니다"
        )
    
    db.delete(spec)
    db.commit()
