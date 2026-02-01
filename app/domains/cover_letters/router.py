from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.shared.database import get_db
from app.domains.users.models import User
from app.domains.auth.dependencies import get_current_user
from .schemas import (
    CoverLetterCreateRequest,
    CoverLetterResponse,
    CoverLetterListResponse,
    CoverLetterDetailResponse,
    CoverLetterDeleteResponse,
)
from .service import (
    create_cover_letter,
    get_cover_letters,
    get_cover_letter_detail,
    delete_cover_letter,
)

router = APIRouter(prefix="/cover-letters", tags=["Cover Letters"])


@router.post("", response_model=CoverLetterResponse, status_code=status.HTTP_201_CREATED)
async def create_cover_letter_api(
    request: CoverLetterCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """자소서 생성"""
    return await create_cover_letter(db, current_user, request)


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
    return get_cover_letter_detail(db, current_user, cover_letter_id)


@router.delete("/{cover_letter_id}", response_model=CoverLetterDeleteResponse)
def delete_cover_letter_api(
    cover_letter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """자소서 삭제"""
    delete_cover_letter(db, current_user, cover_letter_id)
    return CoverLetterDeleteResponse()