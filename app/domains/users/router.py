from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.shared.database import get_db
from .schemas import UserResponse, UserSpecCreate, UserSpecUpdate, UserSpecResponse
from .models import User
from .service import create_user_spec, get_user_spec, update_user_spec, delete_user_spec
from ..auth.dependencies import get_current_user
from ..job_categories.exceptions import JobCategoryNotFoundError

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/me/spec", response_model=UserSpecResponse, status_code=status.HTTP_201_CREATED)
def create_my_spec(
    spec_data: UserSpecCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 스펙 생성
    
    - JWT 토큰의 사용자만 접근 가능
    - 이미 스펙이 존재하면 409 Conflict 반환
    """
    try:
        return create_user_spec(db, current_user, spec_data)
    except JobCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다"
        )


@router.get("/me/spec", response_model=UserSpecResponse)
def get_my_spec(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 스펙 조회
    
    - JWT 토큰의 사용자만 접근 가능
    """
    return get_user_spec(db, current_user)


@router.put("/me/spec", response_model=UserSpecResponse)
def update_my_spec(
    spec_data: UserSpecUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 스펙 수정
    
    - JWT 토큰의 사용자만 접근 가능
    - 부분 업데이트 지원 (제공된 필드만 수정)
    """
    try:
        return update_user_spec(db, current_user, spec_data)
    except JobCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다"
        )


@router.delete("/me/spec", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_spec(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 스펙 삭제
    
    - JWT 토큰의 사용자만 접근 가능
    """
    delete_user_spec(db, current_user)

