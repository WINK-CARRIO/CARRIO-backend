from typing import Optional

from sqlalchemy.orm import Session

from app.domains.companies.models import Company
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
    CoverLetterResponse,
    CoverLetterListResponse,
    CoverLetterListItem,
    CoverLetterDetailResponse,
    CoverLetterItemResponse,
    QuestionResponse,
    AnswerResponse,
)


async def create_cover_letter(
    db: Session,
    user: User,
    request: CoverLetterCreateRequest
) -> CoverLetterResponse:
    """
    자소서 생성
    1. 기본 정보 확인 (UserSpec, Company)
    2. 인재상(DNA) 확보 (DB 조회 -> 없으면 AI 추출 + 저장)
    3. 자소서 생성 + 저장
    """
    user_spec = db.query(UserSpec).filter(UserSpec.user_id == user.id).first()
    if not user_spec:
        raise UserSpecNotFoundException()

    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise CompanyNotFoundException()

    job_category_name = None
    if request.job_category_id:
        job_category = db.query(JobCategory).filter(
            JobCategory.id == request.job_category_id
        ).first()
        if job_category:
            job_category_name = job_category.name

    company_dna = None

    query = db.query(CompanyTalentValue).filter(
        CompanyTalentValue.company_id == request.company_id
    )
    if request.job_category_id:
        talent_record = query.filter(
            CompanyTalentValue.scope == "job_category",
            CompanyTalentValue.job_category_id == request.job_category_id
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
            "preferred_experiences": vals.get("technical_requirements", []) if request.job_category_id else vals.get("preferred_experiences", [])
        }

    else:
        print(f"📡 인재상 데이터 없음. AI 추출 시작... (Company: {company.name})")
        extracted_dna = await run_extraction_pipeline(
            company_name=company.name,
            job_category=job_category_name
        )

        if not extracted_dna:
            raise CoverLetterGenerationFailedException("기업 인재상 분석에 실패하여 자소서를 생성할 수 없습니다.")

        company_dna = extracted_dna

        talent_save_data = {
            "keywords": extracted_dna.get("keywords", []),
            "description": extracted_dna.get("communication_tone", ""),
            "details": extracted_dna.get("ideal_traits", []),
            "core_values": extracted_dna.get("core_values", []),
            "technical_requirements" if request.job_category_id else "preferred_experiences": extracted_dna.get("preferred_experiences", [])
        }

        if request.job_category_id:
            create_job_talent_value(db, request.company_id, request.job_category_id, talent_save_data)
        else:
            create_company_talent_value(db, request.company_id, talent_save_data)

    # 자소서 생성
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

    final_items = result.get("final_result", [])

    question_data = []
    content_data = []

    for req_q in request.questions:
        question_data.append({
            "content": req_q.content,
            "min_length": req_q.min_length,
            "max_length": req_q.max_length
        })

        matched_item = next((item for item in final_items if item["question"] == req_q.content), None)

        if matched_item:
            content_data.append({
                "content": matched_item["answer"],
                "length": len(matched_item["answer"]),
                "guide_comments": matched_item["guide_comments"] # Agent가 생성한 가이드 사용
            })
        else:
            content_data.append({
                "content": "", "length": 0, "guide_comments": ["생성 실패"]
            })

    generation_metadata = {
        "quality_report": result.get("quality_report", {}),
        "status": result.get("status")
    }

    cover_letter = CoverLetter(
        user_id=user.id,
        user_spec_id=user_spec.id,
        company_id=request.company_id,
        job_category_id=request.job_category_id,
        question=question_data,
        content=content_data,
        status="completed",
        generation_metadata=generation_metadata
    )
    db.add(cover_letter)
    db.commit()
    db.refresh(cover_letter)

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

    data = []
    for cl in cover_letters:
        company = db.query(Company).filter(Company.id == cl.company_id).first()
        job_category = None
        if cl.job_category_id:
            job_category = db.query(JobCategory).filter(
                JobCategory.id == cl.job_category_id
            ).first()

        overall_score = None
        if cl.generation_metadata:
            report = cl.generation_metadata.get("quality_report", {})
            score_raw = report.get("overall_score")

            overall_score = score_raw

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
    questions = cover_letter.question or []
    contents = cover_letter.content or []

    for i, q in enumerate(questions):
        answer_data = contents[i] if i < len(contents) else {}

        item_responses.append(CoverLetterItemResponse(
            question=QuestionResponse(
                content=q.get("content", ""),
                min_length=q.get("min_length", 500),
                max_length=q.get("max_length", 700)
            ),
            answer=AnswerResponse(
                content=answer_data.get("content", ""),
                length=answer_data.get("length", 0),
                guide_comments=answer_data.get("guide_comments", [])
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

