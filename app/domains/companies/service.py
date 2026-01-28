from typing import Optional, List, Tuple

from sqlalchemy.orm import Session
from .models import Company
from .schemas import CompanyCreate, CompanyUpdate
from .exceptions import CompanyNotFoundError, CompanyDuplicateError


# 기업 생성
def create_company(db: Session, data: CompanyCreate) -> Company:
    # 기업명 중복 체크
    existing = db.query(Company).filter(Company.name == data.name).first()
    if existing:
        raise CompanyDuplicateError()

    company = Company(
        name=data.name,
        industry=data.industry,
        description=data.description,
        logo_url=data.logo_url,
        website_url=data.website_url,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


# 기업 목록 조회
def get_companies(
    db: Session,
    search: Optional[str] = None,
    sort: str = "name",
    page: int = 1,
    limit: int = 20,
) -> Tuple[int, List[Company]]:
    query = db.query(Company)

    # 기업명 검색
    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))

    total = query.count()

    # 정렬: name=가나다순, latest=최신 등록순
    if sort == "latest":
        query = query.order_by(Company.created_at.desc())
    else:
        query = query.order_by(Company.name.asc())

    companies = query.offset((page - 1) * limit).limit(limit).all()
    return total, companies


# 기업 상세 조회
def get_company(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise CompanyNotFoundError()
    return company


# 기업 수정
def update_company(db: Session, company_id: int, data: CompanyUpdate) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise CompanyNotFoundError()

    # 기업명 변경 시 중복 체크
    if data.name and data.name != company.name:
        existing = db.query(Company).filter(Company.name == data.name).first()
        if existing:
            raise CompanyDuplicateError()

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(company, key, value)

    db.commit()
    db.refresh(company)
    return company


# 기업 삭제
def delete_company(db: Session, company_id: int) -> None:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise CompanyNotFoundError()

    db.delete(company)
    db.commit()
