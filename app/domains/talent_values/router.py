from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import app.shared.agent.node
from app.shared.database import get_db
from app.domains.auth.dependencies import get_admin_user
from app.domains.users.models import User
from app.domains.companies.models import Company
from app.domains.job_categories.models import JobCategory
from app.shared.agent.graph import run_extraction_pipeline

from .schemas import (
    TalentValueUpdate,
    JobTalentValueUpdate,
    JobCategoriesWithTalentValuesResponse,
    CompanyTalentValueResponse,
    JobTalentValueResponse,
    AdminTalentValueResponse,
    AdminJobTalentValueResponse,
)
from .service import (
    get_job_categories_with_talent_values,
    create_company_talent_value,
    create_job_talent_value,
    get_company_talent_values,
    get_job_talent_values,
    update_company_talent_values,
    update_job_talent_values,
    delete_company_talent_values,
    delete_job_talent_values,
)
from .exceptions import TalentValueNotFoundError
from app.domains.companies.exceptions import CompanyNotFoundError
from app.domains.job_categories.exceptions import JobCategoryNotFoundError
from app.shared.agent.exceptions import (
    CompanyResearchError,
    CompanyDNAExtractionError
)

router = APIRouter(tags=["Talent Values"])


# --- 공개 API ---

@router.get("/companies/{company_id}/job-categories", response_model=JobCategoriesWithTalentValuesResponse)
def get_job_categories_with_talent_values_list(
    company_id: int,
    db: Session = Depends(get_db),
):
    """기업별 인재상 보유 직군 목록 조회 (공개)"""
    try:
        return get_job_categories_with_talent_values(db, company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )


@router.post("/companies/{company_id}/talent-values/extract", response_model=CompanyTalentValueResponse)
async def extract_company_talent(
    company_id: int,
    db: Session = Depends(get_db),
):
    """전사 인재상 추출 및 저장"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise CompanyNotFoundError()

    try:
        extracted_dna = await run_extraction_pipeline(company_name=company.name)
    except Exception as e:
        raise CompanyResearchError(f"인재상 추출 파이프라인 에러: {str(e)}")

    if not extracted_dna:
        raise CompanyDNAExtractionError("AI가 유효한 인재상을 추출하지 못했습니다.")

    talent_data = {
        "keywords": extracted_dna.get("keywords", []),
        "description": extracted_dna.get("communication_tone", ""),
        "details": extracted_dna.get("ideal_traits", []),
        "core_values": extracted_dna.get("core_values", []),
        "preferred_experiences": extracted_dna.get("preferred_experiences", [])
    }

    saved_talent = create_company_talent_value(db, company_id, talent_data)

    return {
        "id": saved_talent.id,
        "company_id": company.id,
        "company_name": company.name,
        "talent_values": {"overall": saved_talent.values},
        "extracted_at": saved_talent.extracted_at,
    }


@router.post(
    "/companies/{company_id}/job-categories/{job_category_id}/talent-values/extract",
    response_model=JobTalentValueResponse,
)
async def extract_job_talent(
    company_id: int,
    job_category_id: int,
    db: Session = Depends(get_db),
):
    """직무 인재상 추출 및 저장"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise CompanyNotFoundError()

    job_cat = db.query(JobCategory).filter(JobCategory.id == job_category_id).first()
    if not job_cat:
        raise JobCategoryNotFoundError()

    try:
        extracted_dna = await run_extraction_pipeline(
            company_name=company.name,
            job_category=job_cat.name
        )
    except Exception as e:
        raise CompanyResearchError(f"직무 인재상 추출 파이프라인 에러: {str(e)}")

    if not extracted_dna:
        raise CompanyDNAExtractionError("유효한 인재상을 추출하지 못했습니다.")

    talent_data = {
        "keywords": extracted_dna.get("keywords", []),
        "description": extracted_dna.get("communication_tone", ""),
        "details": extracted_dna.get("ideal_traits", []),
        "technical_requirements": extracted_dna.get("preferred_experiences", [])
    }

    saved_talent = create_job_talent_value(db, company_id, job_category_id, talent_data)

    return {
        "id": saved_talent.id,
        "company_id": company.id,
        "company_name": company.name,
        "job_category_id": job_cat.id,
        "job_category_name": job_cat.name,
        "talent_values": {"job_specific": saved_talent.values},
        "extracted_at": saved_talent.extracted_at,
    }


@router.get("/companies/{company_id}/talent-values", response_model=CompanyTalentValueResponse)
def get_company_talent(
    company_id: int,
    db: Session = Depends(get_db),
):
    """전사 인재상 조회 (공개)"""
    try:
        return get_company_talent_values(db, company_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
    except TalentValueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전사 인재상이 등록되지 않았습니다",
        )


@router.get(
    "/companies/{company_id}/job-categories/{job_category_id}/talent-values",
    response_model=JobTalentValueResponse,
)
def get_job_talent(
    company_id: int,
    job_category_id: int,
    db: Session = Depends(get_db),
):
    """직무별 인재상 조회 (공개)"""
    try:
        return get_job_talent_values(db, company_id, job_category_id)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
    except JobCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다",
        )
    except TalentValueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직무 인재상이 등록되지 않았습니다",
        )


# --- Admin API ---

@router.put("/admin/companies/{company_id}/talent-values", response_model=AdminTalentValueResponse)
def update_company_talent(
    company_id: int,
    body: TalentValueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """전사 인재상 수정 (Admin)"""
    try:
        return update_company_talent_values(db, company_id, body)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
    except TalentValueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전사 인재상이 등록되지 않았습니다",
        )


@router.put(
    "/admin/companies/{company_id}/job-categories/{job_category_id}/talent-values",
    response_model=AdminJobTalentValueResponse,
)
def update_job_talent(
    company_id: int,
    job_category_id: int,
    body: JobTalentValueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """직무 인재상 수정 (Admin)"""
    try:
        return update_job_talent_values(db, company_id, job_category_id, body)
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
    except JobCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다",
        )
    except TalentValueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직무 인재상이 등록되지 않았습니다",
        )


@router.delete("/admin/companies/{company_id}/talent-values")
def delete_company_talent(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """전사 인재상 삭제 (Admin)"""
    try:
        delete_company_talent_values(db, company_id)
        return {"message": "전사 인재상이 삭제되었습니다"}
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
    except TalentValueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전사 인재상이 등록되지 않았습니다",
        )


@router.delete(
    "/admin/companies/{company_id}/job-categories/{job_category_id}/talent-values",
)
def delete_job_talent(
    company_id: int,
    job_category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """직무 인재상 삭제 (Admin)"""
    try:
        delete_job_talent_values(db, company_id, job_category_id)
        return {"message": "직무 인재상이 삭제되었습니다"}
    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
    except JobCategoryNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직군을 찾을 수 없습니다",
        )
    except TalentValueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직무 인재상이 등록되지 않았습니다",
        )
