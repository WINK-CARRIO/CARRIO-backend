from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import func

from app.domains.companies.models import Company
from app.domains.companies.exceptions import CompanyNotFoundError
from app.domains.job_categories.models import JobCategory
from app.domains.job_categories.exceptions import JobCategoryNotFoundError
from .models import CompanyTalentValue
from .schemas import JobTalentValueResponse, CompanyTalentValueResponse, TalentValueUpdate, JobTalentValueUpdate
from .exceptions import TalentValueNotFoundError
from ...shared.agent.exceptions import CompanyDNAExtractionError, CompanyResearchError
from ...shared.agent.graph import run_extraction_pipeline


def _get_company_or_raise(db: Session, company_id: int) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise CompanyNotFoundError()
    return company


def _get_job_category_or_raise(db: Session, job_category_id: int) -> JobCategory:
    job_category = db.query(JobCategory).filter(JobCategory.id == job_category_id).first()
    if not job_category:
        raise JobCategoryNotFoundError()
    return job_category


def _get_company_talent_or_raise(db: Session, company_id: int) -> CompanyTalentValue:
    talent = db.query(CompanyTalentValue).filter(
        CompanyTalentValue.company_id == company_id,
        CompanyTalentValue.scope == "company",
        CompanyTalentValue.job_category_id.is_(None),
    ).first()
    if not talent:
        raise TalentValueNotFoundError()
    return talent


def _get_job_talent_or_raise(db: Session, company_id: int, job_category_id: int) -> CompanyTalentValue:
    talent = db.query(CompanyTalentValue).filter(
        CompanyTalentValue.company_id == company_id,
        CompanyTalentValue.scope == "job_category",
        CompanyTalentValue.job_category_id == job_category_id,
    ).first()
    if not talent:
        raise TalentValueNotFoundError()
    return talent


# 기업별 인재상 보유 직군 목록 조회
def get_job_categories_with_talent_values(db: Session, company_id: int) -> dict:
    company = _get_company_or_raise(db, company_id)

    talents = db.query(CompanyTalentValue, JobCategory).join(
        JobCategory, CompanyTalentValue.job_category_id == JobCategory.id
    ).filter(
        CompanyTalentValue.company_id == company_id,
        CompanyTalentValue.scope == "job_category",
    ).all()

    return {
        "company_id": company.id,
        "company_name": company.name,
        "job_categories": [
            {
                "job_category_id": job_category.id,
                "job_category_name": job_category.name,
                "extracted_at": talent.extracted_at,
            }
            for talent, job_category in talents
        ],
    }


# 전사 인재상 저장 (Upsert)
def create_company_talent_value(db: Session, company_id: int, data: Dict[str, Any]) -> CompanyTalentValue:
    _get_company_or_raise(db, company_id)

    existing = db.query(CompanyTalentValue).filter(
        CompanyTalentValue.company_id == company_id,
        CompanyTalentValue.scope == "company",
        CompanyTalentValue.job_category_id.is_(None)
    ).first()

    if existing:
        existing.values = data
        existing.last_updated = func.now()
        db.commit()
        db.refresh(existing)
        return existing

    new_talent = CompanyTalentValue(
        company_id=company_id,
        scope="company",
        job_category_id=None,
        values=data
    )
    db.add(new_talent)
    db.commit()
    db.refresh(new_talent)
    return new_talent


# 직무 인재상 저장
def create_job_talent_value(db: Session, company_id: int, job_category_id: int, data: Dict[str, Any]) -> CompanyTalentValue:
    _get_company_or_raise(db, company_id)
    _get_job_category_or_raise(db, job_category_id)

    existing = db.query(CompanyTalentValue).filter(
        CompanyTalentValue.company_id == company_id,
        CompanyTalentValue.scope == "job_category",
        CompanyTalentValue.job_category_id == job_category_id
    ).first()

    if existing:
        existing.values = data
        existing.last_updated = func.now()
        db.commit()
        db.refresh(existing)
        return existing

    new_talent = CompanyTalentValue(
        company_id=company_id,
        scope="job_category",
        job_category_id=job_category_id,
        values=data
    )
    db.add(new_talent)
    db.commit()
    db.refresh(new_talent)
    return new_talent


# job_category_id 있는지에 따라 전사, 직무 따로 처리
async def _process_talent_extraction(
    db: Session,
    company_id: int,
    job_category_id: Optional[int] = None
) -> Union[CompanyTalentValueResponse, JobTalentValueResponse]:

    company = _get_company_or_raise(db, company_id)

    job_category = None
    if job_category_id:
        job_category = _get_job_category_or_raise(db, job_category_id)

    job_name = job_category.name if job_category else None
    try:
        extracted_dna = await run_extraction_pipeline(
            company_name=company.name,
            job_category=job_name
        )
    except Exception as e:
        target = "직무" if job_category_id else "전사"
        raise CompanyResearchError(f"{target} 인재상 추출 파이프라인 에러: {str(e)}")

    if not extracted_dna:
        raise CompanyDNAExtractionError("AI가 유효한 인재상을 추출하지 못했습니다.")

    talent_data = {
        "keywords": extracted_dna.get("keywords", []),
        "description": extracted_dna.get("communication_tone", ""),
        "details": extracted_dna.get("ideal_traits", []),
        "core_values": extracted_dna.get("core_values", []),
    }

    experiences = extracted_dna.get("preferred_experiences", [])
    if job_category_id:
        talent_data["technical_requirements"] = experiences
    else:
        talent_data["preferred_experiences"] = experiences

    if job_category_id:
        saved_talent = create_job_talent_value(db, company_id, job_category_id, talent_data)

        overall_talent = db.query(CompanyTalentValue).filter(
            CompanyTalentValue.company_id == company_id,
            CompanyTalentValue.scope == "company",
            CompanyTalentValue.job_category_id.is_(None)
        ).first()

        overall_values = overall_talent.values if overall_talent else {}

        return JobTalentValueResponse(
            id=saved_talent.id,
            company_id=company.id,
            company_name=company.name,
            job_category_id=job_category.id,
            job_category_name=job_category.name,

            talent_values={
                "overall": overall_values,
                "job_specific": saved_talent.values
            },
            extracted_at=saved_talent.extracted_at
        )
    else:
        saved_talent = create_company_talent_value(db, company_id, talent_data)

        return CompanyTalentValueResponse(
            id=saved_talent.id,
            company_id=company.id,
            company_name=company.name,
            talent_values={"overall": saved_talent.values},
            extracted_at=saved_talent.extracted_at
        )


# 전사 인재상 추출
async def extract_and_save_company_talent(db: Session, company_id: int) -> CompanyTalentValueResponse:
    return await _process_talent_extraction(db, company_id, job_category_id=None)


# 직무별 인재상 추출
async def extract_and_save_job_talent(db: Session, company_id: int, job_category_id: int) -> JobTalentValueResponse:
    return await _process_talent_extraction(db, company_id, job_category_id=job_category_id)


# 전사 인재상 조회
def get_company_talent_values(db: Session, company_id: int) -> dict:
    company = _get_company_or_raise(db, company_id)
    talent_value = _get_company_talent_or_raise(db, company_id)

    return {
        "id": talent_value.id,
        "company_id": company.id,
        "company_name": company.name,
        "talent_values": {"overall": talent_value.values},
        "extracted_at": talent_value.extracted_at,
    }


# 직무별 인재상 조회
def get_job_talent_values(db: Session, company_id: int, job_category_id: int) -> dict:
    company = _get_company_or_raise(db, company_id)
    job_category = _get_job_category_or_raise(db, job_category_id)

    job_talent = _get_job_talent_or_raise(db, company_id, job_category_id)

    return {
        "id": job_talent.id,
        "company_id": company.id,
        "company_name": company.name,
        "job_category_id": job_category.id,
        "job_category_name": job_category.name,
        "talent_values": {"job_specific": job_talent.values},
        "extracted_at": job_talent.extracted_at,
    }


# 전사 인재상 수정
def update_company_talent_values(db: Session, company_id: int, data: TalentValueUpdate) -> dict:
    _get_company_or_raise(db, company_id)
    talent_value = _get_company_talent_or_raise(db, company_id)

    talent_value.values = data.model_dump()
    db.commit()
    db.refresh(talent_value)

    return {
        "id": talent_value.id,
        "company_id": talent_value.company_id,
        "talent_values": {"overall": talent_value.values},
        "extracted_at": talent_value.extracted_at,
    }


# 직무 인재상 수정
def update_job_talent_values(
    db: Session, company_id: int, job_category_id: int, data: JobTalentValueUpdate
) -> dict:
    _get_company_or_raise(db, company_id)
    _get_job_category_or_raise(db, job_category_id)
    job_talent = _get_job_talent_or_raise(db, company_id, job_category_id)

    job_talent.values = data.job_specific.model_dump()
    db.commit()
    db.refresh(job_talent)

    return {
        "id": job_talent.id,
        "company_id": job_talent.company_id,
        "job_category_id": job_talent.job_category_id,
        "talent_values": {"job_specific": job_talent.values},
        "extracted_at": job_talent.extracted_at,
    }


# 전사 인재상 삭제
def delete_company_talent_values(db: Session, company_id: int) -> None:
    _get_company_or_raise(db, company_id)
    talent_value = _get_company_talent_or_raise(db, company_id)

    db.delete(talent_value)
    db.commit()


# 직무 인재상 삭제
def delete_job_talent_values(db: Session, company_id: int, job_category_id: int) -> None:
    _get_company_or_raise(db, company_id)
    _get_job_category_or_raise(db, job_category_id)
    job_talent = _get_job_talent_or_raise(db, company_id, job_category_id)

    db.delete(job_talent)
    db.commit()
