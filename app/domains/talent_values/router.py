from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.domains.auth.dependencies import get_admin_user
from app.domains.companies.exceptions import CompanyNotFoundError
from app.domains.job_categories.exceptions import JobCategoryNotFoundError
from app.domains.users.models import User
from app.shared.agent.exceptions import (
    CompanyResearchError,
    CompanyDNAExtractionError
)
from app.shared.database import get_db
from .exceptions import TalentValueNotFoundError
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
    get_company_talent_values,
    get_job_talent_values,
    update_company_talent_values,
    update_job_talent_values,
    delete_company_talent_values,
    delete_job_talent_values,
    extract_and_save_company_talent,
    extract_and_save_job_talent,
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

@router.post(
    "/admin/companies/{company_id}/extract-talent-values",
    response_model=CompanyTalentValueResponse
)
async def extract_company_talent(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """전사 인재상 추출 및 저장 (Admin)"""
    try:
        return await extract_and_save_company_talent(db, company_id)

    except CompanyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="기업을 찾을 수 없습니다",
        )
    except (CompanyResearchError, CompanyDNAExtractionError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 내부 오류: {str(e)}",
        )


@router.post(
    "/admin/companies/{company_id}/job-categories/{job_category_id}/extract-talent-values",
    response_model=JobTalentValueResponse,
)
async def extract_job_talent(
    company_id: int,
    job_category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """직무 인재상 추출 및 저장 (Admin)"""
    try:
        return await extract_and_save_job_talent(db, company_id, job_category_id)

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
    except (CompanyResearchError, CompanyDNAExtractionError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 내부 오류: {str(e)}",
        )

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
