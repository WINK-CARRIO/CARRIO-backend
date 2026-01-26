# 회원가입 api 정의 , service.py 이용, schemas.py(요청/응답) 이용
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.shared.database import get_db
from .schemas import UserResponse, UserSpecCreate, UserSpecUpdate, UserSpecResponse
from .models import User
from .service import create_user_spec, get_user_spec, update_user_spec, delete_user_spec
from ..auth.dependencies import get_current_user
# from .service import create_user
from ..auth.schemas import RegisterRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/{user_id}/spec", response_model=UserSpecResponse, status_code=status.HTTP_201_CREATED)
def create_spec(
    user_id: int,
    spec_data: UserSpecCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 스펙 생성
    
    - 본인만 접근 가능
    - 이미 스펙이 존재하면 409 Conflict 반환
    """
    # 권한 검증: 본인만 접근 가능
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 스펙을 생성할 수 없습니다"
        )
    
    return create_user_spec(db, user_id, spec_data)


@router.get("/{user_id}/spec", response_model=UserSpecResponse)
def get_spec(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 스펙 조회
    
    - 본인만 접근 가능
    """
    # 권한 검증: 본인만 접근 가능
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 스펙을 조회할 수 없습니다"
        )
    
    return get_user_spec(db, user_id)


@router.put("/{user_id}/spec", response_model=UserSpecResponse)
def update_spec(
    user_id: int,
    spec_data: UserSpecUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 스펙 수정
    
    - 본인만 접근 가능
    - 부분 업데이트 지원 (제공된 필드만 수정)
    """
    # 권한 검증: 본인만 접근 가능
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 스펙을 수정할 수 없습니다"
        )
    
    return update_user_spec(db, user_id, spec_data)


@router.delete("/{user_id}/spec", status_code=status.HTTP_200_OK)
def delete_spec(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 스펙 삭제
    
    - 본인만 접근 가능
    """
    # 권한 검증: 본인만 접근 가능
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 스펙을 삭제할 수 없습니다"
        )
    
    delete_user_spec(db, user_id)
    return {"message": "스펙이 삭제되었습니다"}

