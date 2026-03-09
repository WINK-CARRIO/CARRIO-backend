from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.shared.database import get_db
from app.domains.users.models import User
from app.domains.auth.dependencies import get_current_user
from .schemas import (
    CoverLetterCreateRequest,
    CoverLetterUpdateRequest,
    CoverLetterResponse,
    CoverLetterListResponse,
    CoverLetterDetailResponse,
)
from .service import (
    create_cover_letter,
    get_cover_letters,
    get_cover_letter_detail,
    update_cover_letter,
    delete_cover_letter,
)
from .exceptions import (
    CoverLetterForbiddenException,
    CoverLetterNotFoundException,
    CoverLetterGenerationFailedException,
    CompanyNotFoundException
)
from ..job_categories.exceptions import JobCategoryNotFoundError
from ..users.exceptions import UserSpecNotFoundException

router = APIRouter(prefix="/cover-letters", tags=["Cover Letters"])


@router.post("", response_model=CoverLetterResponse, status_code=status.HTTP_201_CREATED)
async def create_cover_letter_api(
    request: CoverLetterCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """자소서 생성"""
    try:
        return await create_cover_letter(db, current_user, request)

    except CompanyNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다"
        )
    except JobCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다"
        )
    except UserSpecNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자 스펙을 먼저 등록해주세요"
        )
    except CoverLetterGenerationFailedException as e:
        print(f"자소서 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자소서 생성에 실패했습니다. 잠시 후 다시 시도해주세요."
        )
    except Exception as e:
        print(f"자소서 생성 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자소서 생성 중 오류가 발생했습니다"
        )


@router.get("", response_model=CoverLetterListResponse)
def get_cover_letters_api(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=10, ge=1, le=100, description="페이지당 항목 수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """자소서 목록 조회"""
    return get_cover_letters(db, current_user, page, limit)


@router.get("/{cover_letter_id}", response_model=CoverLetterDetailResponse)
def get_cover_letter_detail_api(
    cover_letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """자소서 상세 조회"""
    try:
        return get_cover_letter_detail(db, current_user, cover_letter_id)

    except CoverLetterNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="자소서를 찾을 수 없습니다"
        )
    except CoverLetterForbiddenException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 자소서에 대한 접근 권한이 없습니다"
        )


@router.put("/{cover_letter_id}", response_model=CoverLetterResponse)
def update_cover_letter_api(
    cover_letter_id: int,
    request: CoverLetterUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """자소서 수정 - 본인 자소서만 수정 가능"""
    try:
        return update_cover_letter(db, current_user, cover_letter_id, request)

    except CoverLetterNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="자소서를 찾을 수 없습니다"
        )
    except CoverLetterForbiddenException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 자소서에 대한 접근 권한이 없습니다"
        )


@router.delete("/{cover_letter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cover_letter_api(
    cover_letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """자소서 삭제"""
    try:
        delete_cover_letter(db, current_user, cover_letter_id)
        return None

    except CoverLetterNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="자소서를 찾을 수 없습니다"
        )
    except CoverLetterForbiddenException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 자소서에 대한 접근 권한이 없습니다"
        )