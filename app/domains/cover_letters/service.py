import asyncio
from functools import partial
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.domains.companies.models import Company
from app.shared.database import SessionLocal
from app.domains.job_categories.models import JobCategory
from app.domains.talent_values.models import CompanyTalentValue
from app.domains.talent_values.service import create_company_talent_value, create_job_talent_value
from app.domains.users.exceptions import UserSpecNotFoundException
from app.domains.users.models import User, UserSpec
from app.shared.agent.graph import run_extraction_pipeline, run_generation_pipeline
from .exceptions import (
    CoverLetterNotFoundException,
    CoverLetterGenerationFailedException,
    CoverLetterForbiddenException,
    CompanyNotFoundException,
)
from .models import CoverLetter
from .schemas import (
    CoverLetterCreateRequest,
    CoverLetterUpdateRequest,
    CoverLetterResponse,
    CoverLetterListResponse,
    CoverLetterListItem,
    CoverLetterDetailResponse,
    CoverLetterItemResponse,
    QuestionResponse,
    AnswerResponse,
)
from ..job_categories.exceptions import JobCategoryNotFoundError


def _fetch_pipeline_data_sync(user_id: int, company_id: int, job_category_id: Optional[int]):
    """
    동기 방식 db 조회 (별도 스레드에서 실행)
    SQLAlchemy Session은 thread-safe하지 않으므로 executor 내에서 새 Session 생성
    """
    db = SessionLocal()
    try:
        return _fetch_pipeline_data_query(db, user_id, company_id, job_category_id)
    finally:
        db.close()


def _fetch_pipeline_data_query(db: Session, user_id: int, company_id: int, job_category_id: Optional[int]):
    """실제 DB 조회 로직"""
    user_spec = db.query(UserSpec).filter(UserSpec.user_id == user_id).first()
    if not user_spec:
        raise UserSpecNotFoundException()

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise CompanyNotFoundException()

    job_category_name = None
    if job_category_id:
        job_category = db.query(JobCategory).filter(JobCategory.id == job_category_id).first()
        if not job_category:
            raise JobCategoryNotFoundError()
        job_category_name = job_category.name

    # 있는 경우만 찾아 쓰고 없는 경우는 밑에 별도 생성
    company_dna = None
    query = db.query(CompanyTalentValue).filter(CompanyTalentValue.company_id == company_id)

    if job_category_id:
        talent_record = query.filter(
            CompanyTalentValue.scope == "job_category",
            CompanyTalentValue.job_category_id == job_category_id
        ).first()
    else:
        talent_record = query.filter(
            CompanyTalentValue.scope == "company",
            CompanyTalentValue.job_category_id.is_(None)
        ).first()

    if talent_record:
        vals = talent_record.values
        company_dna = {
            "core_values": vals.get("core_values", []),
            "ideal_traits": vals.get("details", []),
            "keywords": vals.get("keywords", []),
            "communication_tone": vals.get("description", ""),
            "preferred_experiences": vals.get("technical_requirements", []) if job_category_id else vals.get("preferred_experiences", [])
        }

    return {
        "user_spec": user_spec,
        "company": company,
        "job_category_name": job_category_name,
        "existing_dna": company_dna
    }


def _save_cover_letter_result(
    db: Session,
    user: User,
    user_spec_id: int,
    request: CoverLetterCreateRequest,
    result: Dict[str, Any]
) -> CoverLetter:
    """생성 결과 파싱하고 DB 저장"""

    final_items = result.get("final_result", [])
    items_data = []

    for i, req_q in enumerate(request.questions):
        question_obj = {
            "content": req_q.content,
            "min_length": req_q.min_length,
            "max_length": req_q.max_length
        }

        # 1순위: question_index 기반 매칭 (1-based)
        matched_item = next(
            (item for item in final_items if item.get("question_index") == i + 1), None
        )
        # 2순위: LLM이 question_index를 빠뜨린 경우 텍스트 fallback
        if not matched_item:
            matched_item = next(
                (item for item in final_items if item.get("question") == req_q.content), None
            )

        if matched_item:
            answer_obj = {
                "content": matched_item["answer"],
                "length": len(matched_item["answer"]),
                "guide_comments": matched_item["guide_comments"]
            }
        else:
            answer_obj = {
                "content": "", "length": 0, "guide_comments": ["생성 실패"]
            }

        items_data.append({"question": question_obj, "answer": answer_obj})

    generation_metadata = {
        "quality_report": result.get("quality_report", {}),
        "status": result.get("status")
    }

    cover_letter = CoverLetter(
        user_id=user.id,
        user_spec_id=user_spec_id,
        company_id=request.company_id,
        job_category_id=request.job_category_id,
        items=items_data,
        status="completed",
        generation_metadata=generation_metadata
    )
    db.add(cover_letter)
    db.commit()
    db.refresh(cover_letter)

    return cover_letter


async def _ensure_company_dna(
    db: Session,
    company_id: int,
    company_name: str,
    job_category_id: Optional[int],
    job_category_name: Optional[str],
    existing_dna: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """인재상 확보 로직 (DB에 없는 경우 추출해서 반환)"""

    if existing_dna:
        return existing_dna

    print(f"📡 인재상 데이터 없음. AI 추출 시작... (Company: {company_name})")

    extracted_dna = await run_extraction_pipeline(
        company_name=company_name,
        job_category=job_category_name
    )

    if not extracted_dna:
        raise CoverLetterGenerationFailedException("기업 인재상 분석에 실패하여 자소서를 생성할 수 없습니다.")

    talent_save_data = {
        "keywords": extracted_dna.get("keywords", []),
        "description": extracted_dna.get("communication_tone", ""),
        "details": extracted_dna.get("ideal_traits", []),
        "core_values": extracted_dna.get("core_values", []),
        "technical_requirements" if job_category_id else "preferred_experiences": extracted_dna.get("preferred_experiences", [])
    }

    if job_category_id:
        create_job_talent_value(db, company_id, job_category_id, talent_save_data)
    else:
        create_company_talent_value(db, company_id, talent_save_data)

    return extracted_dna

async def create_cover_letter(
    db: Session,
    user: User,
    request: CoverLetterCreateRequest
) -> CoverLetterResponse:
    """자소서 생성"""

    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(
        None,
        partial(_fetch_pipeline_data_sync, user.id, request.company_id, request.job_category_id)
    )

    user_spec = data["user_spec"]
    company = data["company"]
    job_category_name = data["job_category_name"]
    existing_dna = data["existing_dna"]

    company_dna = await _ensure_company_dna(
        db=db,
        company_id=request.company_id,
        company_name=company.name,
        job_category_id=request.job_category_id,
        job_category_name=job_category_name,
        existing_dna=existing_dna
    )

    questions_for_agent = [
        {"content": q.content, "min_length": q.min_length, "max_length": q.max_length}
        for q in request.questions
    ]

    user_spec_data = {
        "structured_data": user_spec.structured_data,
        "free_experiences": user_spec.free_experiences
    }

    company_info_data = {
        "name": company.name,
        "industry": company.industry,
        "description": company.description
    }

    result = await run_generation_pipeline(
        user_spec=user_spec_data,
        company_dna=company_dna,
        company_info=company_info_data,
        questions=questions_for_agent
    )

    if result.get("status") == "failed":
        raise CoverLetterGenerationFailedException(
            result.get("error", "자소서 생성 중 오류가 발생했습니다")
        )

    cover_letter = _save_cover_letter_result(
        db=db,
        user=user,
        user_spec_id=user_spec.id,
        request=request,
        result=result
    )

    return _build_cover_letter_response(
        cover_letter=cover_letter,
        company_name=company.name,
        job_category_name=job_category_name
    )


def get_cover_letters(
    db: Session,
    user: User,
    page: int = 1,
    limit: int = 10
) -> CoverLetterListResponse:
    """자소서 목록 조회"""
    total = db.query(CoverLetter).filter(
        CoverLetter.user_id == user.id
    ).count()

    offset = (page - 1) * limit
    cover_letters = db.query(CoverLetter).filter(
        CoverLetter.user_id == user.id
    ).order_by(
        CoverLetter.created_at.desc()
    ).offset(offset).limit(limit).all()

    if not cover_letters:
        return CoverLetterListResponse(total=total, page=page, limit=limit, data=[])

    # N+1 문제 개선하기 위해 필요한 자료들 먼저 매핑함
    company_ids = {cl.company_id for cl in cover_letters}
    job_category_ids = {cl.job_category_id for cl in cover_letters if cl.job_category_id}
    companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
    company_map = {c.id: c for c in companies}

    job_category_map = {}
    if job_category_ids:
        job_categories = db.query(JobCategory).filter(JobCategory.id.in_(job_category_ids)).all()
        job_category_map = {jc.id: jc for jc in job_categories}

    data = []
    for cl in cover_letters:
        company = company_map.get(cl.company_id)
        job_category = job_category_map.get(cl.job_category_id)

        overall_score = None
        if cl.generation_metadata:
            report = cl.generation_metadata.get("quality_report", {})
            overall_score = report.get("overall_score")

        data.append(CoverLetterListItem(
            id=cl.id,
            company_name=company.name if company else "Unknown",
            job_category_name=job_category.name if job_category else None,
            status=cl.status,
            overall_score=overall_score,
            created_at=cl.created_at
        ))

    return CoverLetterListResponse(
        total=total,
        page=page,
        limit=limit,
        data=data
    )


def get_cover_letter_detail(
    db: Session,
    user: User,
    cover_letter_id: int
) -> CoverLetterDetailResponse:
    """자소서 상세 조회"""
    cover_letter = db.query(CoverLetter).filter(
        CoverLetter.id == cover_letter_id
    ).first()

    if not cover_letter:
        raise CoverLetterNotFoundException()

    if cover_letter.user_id != user.id:
        raise CoverLetterForbiddenException()

    company = db.query(Company).filter(Company.id == cover_letter.company_id).first()
    company_name = company.name if company else "Unknown"

    job_category_name = None
    if cover_letter.job_category_id:
        job_category = db.query(JobCategory).filter(
            JobCategory.id == cover_letter.job_category_id
        ).first()
        if job_category:
            job_category_name = job_category.name

    cover_letter_response = _build_cover_letter_response(
        cover_letter=cover_letter,
        company_name=company_name,
        job_category_name=job_category_name
    )

    matching_analysis = None
    if cover_letter.generation_metadata:
        matching_analysis = cover_letter.generation_metadata.get("quality_report")

    return CoverLetterDetailResponse(
        cover_letter=cover_letter_response,
        matching_analysis=matching_analysis
    )


def update_cover_letter(
    db: Session,
    user: User,
    cover_letter_id: int,
    request: CoverLetterUpdateRequest
) -> CoverLetterResponse:
    """자소서 수정"""
    cover_letter = db.query(CoverLetter).filter(
        CoverLetter.id == cover_letter_id
    ).first()

    if not cover_letter:
        raise CoverLetterNotFoundException()

    if cover_letter.user_id != user.id:
        raise CoverLetterForbiddenException()

    # 기존 items JSONB 업데이트
    existing_items = cover_letter.items or []
    
    # request.items를 순회하며 question.content로 매칭하여 answer.content 업데이트
    for update_item in request.items:
        question_content = update_item.question.content
        
        # 기존 items에서 question.content가 일치하는 항목 찾기
        for existing_item in existing_items:
            if existing_item.get("question", {}).get("content") == question_content:
                # answer.content 업데이트
                existing_item["answer"]["content"] = update_item.answer.content
                # answer.length 재계산
                existing_item["answer"]["length"] = len(update_item.answer.content)
                # guide_comments는 기존 값 유지
                break
    
    # JSONB in-place 수정이므로 flag_modified 필수
    cover_letter.items = existing_items
    flag_modified(cover_letter, "items")
    
    db.commit()
    db.refresh(cover_letter)

    # 응답 생성
    company = db.query(Company).filter(Company.id == cover_letter.company_id).first()
    company_name = company.name if company else "Unknown"

    job_category_name = None
    if cover_letter.job_category_id:
        job_category = db.query(JobCategory).filter(
            JobCategory.id == cover_letter.job_category_id
        ).first()
        if job_category:
            job_category_name = job_category.name

    return _build_cover_letter_response(
        cover_letter=cover_letter,
        company_name=company_name,
        job_category_name=job_category_name
    )


def delete_cover_letter(
    db: Session,
    user: User,
    cover_letter_id: int
) -> None:
    """자소서 삭제"""
    cover_letter = db.query(CoverLetter).filter(
        CoverLetter.id == cover_letter_id
    ).first()

    if not cover_letter:
        raise CoverLetterNotFoundException()

    if cover_letter.user_id != user.id:
        raise CoverLetterForbiddenException()

    db.delete(cover_letter)
    db.commit()


def _build_cover_letter_response(
    cover_letter: CoverLetter,
    company_name: str,
    job_category_name: Optional[str]
) -> CoverLetterResponse:
    """CoverLetterResponse 생성 헬퍼"""
    item_responses = []
    items = cover_letter.items or []

    for item in items:
        q = item.get("question", {})
        a = item.get("answer", {})

        item_responses.append(CoverLetterItemResponse(
            question=QuestionResponse(
                content=q.get("content", ""),
                min_length=q.get("min_length", 500),
                max_length=q.get("max_length", 700)
            ),
            answer=AnswerResponse(
                content=a.get("content", ""),
                length=a.get("length", 0),
                guide_comments=a.get("guide_comments", [])
            )
        ))

    return CoverLetterResponse(
        id=cover_letter.id,
        user_id=cover_letter.user_id,
        company_id=cover_letter.company_id,
        company_name=company_name,
        job_category_id=cover_letter.job_category_id,
        job_category_name=job_category_name,
        status=cover_letter.status,
        created_at=cover_letter.created_at,
        items=item_responses
    )

