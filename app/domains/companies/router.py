from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.shared.database import get_db
from app.domains.auth.dependencies import get_admin_user
from app.domains.users.models import User
from .schemas import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from .service import create_company, get_companies, get_company, update_company, delete_company
from .exceptions import CompanyNotFoundError, CompanyDuplicateError

router = APIRouter(tags=["Companies"])


@router.post("/admin/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create(
    body: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    try:
        return create_company(db, body)
    except CompanyDuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 기업명입니다",
        )


@router.get("/companies", response_model=CompanyListResponse)
def list_all(
    search: Optional[str] = Query(default=None),
    sort: str = Query(default="name", pattern="^(name|latest)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total, companies = get_companies(db, search=search, sort=sort, page=page, limit=limit)
    return CompanyListResponse(total=total, page=page, limit=limit, data=companies)


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def detail(
    company_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_company(db, company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )


@router.put("/admin/companies/{company_id}", response_model=CompanyResponse)
def update(
    company_id: int,
    body: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    try:
        return update_company(db, company_id, body)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
    except CompanyDuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 기업명입니다",
        )


@router.delete("/admin/companies/{company_id}")
def delete(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    try:
        delete_company(db, company_id)
        return {"message": "기업이 삭제되었습니다"}
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
