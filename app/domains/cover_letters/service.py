from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

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
from .exceptions import (
    CoverLetterNotFoundException,
    CoverLetterGenerationFailedException,
    CoverLetterForbiddenException,
    CompanyNotFoundException,
)
from app.domains.users.models import User, UserSpec
from app.domains.users.exceptions import UserSpecNotFoundException
from app.domains.companies.models import Company
from app.domains.job_categories.models import JobCategory
from app.shared.agent.graph import run_cover_letter_pipeline


async def create_cover_letter(
    db: Session,
    user: User,
    request: CoverLetterCreateRequest
) -> CoverLetterResponse:
    """자소서 생성"""
    # 사용자 스펙 확인
    user_spec = db.query(UserSpec).filter(UserSpec.user_id == user.id).first()
    if not user_spec:
        raise UserSpecNotFoundException()

    # 기업 정보 확인
    company = db.query(Company).filter(Company.id == request.company_id).first()
    if not company:
        raise CompanyNotFoundException()

    # 직군 정보 확인 (선택적)
    job_category_name = None
    if request.job_category_id:
        job_category = db.query(JobCategory).filter(
            JobCategory.id == request.job_category_id
        ).first()
        if job_category:
            job_category_name = job_category.name

    # 질문 content만 추출
    question_contents = [q.content for q in request.questions]

    # 에이전트 파이프라인 실행
    result = await run_cover_letter_pipeline(
        user_id=user.id,
        company_id=request.company_id,
        job_category_id=request.job_category_id,
        questions=question_contents,
        db=db
    )

    if result.get("status") == "failed":
        raise CoverLetterGenerationFailedException(
            result.get("error", "자소서 생성 중 오류가 발생했습니다")
        )

    # 답변 파싱 (final_cover_letter는 \n\n으로 구분됨)
    final_cover_letter = result.get("final_cover_letter", "")
    answers = final_cover_letter.split("\n\n") if final_cover_letter else []

    # items JSONB 배열 생성
    items_data = []
    for i, question in enumerate(request.questions):
        answer_content = answers[i] if i < len(answers) else ""
        answer_length = len(answer_content)

        # 가이드 코멘트 생성 (길이 기반)
        guide_comments = _generate_guide_comments(
            answer_content=answer_content,
            min_length=question.min_length,
            max_length=question.max_length
        )

        items_data.append({
            "question": {
                "content": question.content,
                "min_length": question.min_length,
                "max_length": question.max_length
            },
            "answer": {
                "content": answer_content,
                "length": answer_length,
                "guide_comments": guide_comments
            }
        })

    # generation_metadata 구성
    generation_metadata = {
        "quality_report": result.get("quality_report", {}),
        "metadata": result.get("generation_metadata", {})
    }

    # CoverLetter 생성
    cover_letter = CoverLetter(
        user_id=user.id,
        user_spec_id=user_spec.id,
        company_id=request.company_id,
        job_category_id=request.job_category_id,
        items=items_data,
        status="completed",
        generation_metadata=generation_metadata
    )
    db.add(cover_letter)
    db.commit()
    db.refresh(cover_letter)

    # 응답 생성
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
    # 전체 개수
    total = db.query(CoverLetter).filter(
        CoverLetter.user_id == user.id
    ).count()

    # 페이지네이션
    offset = (page - 1) * limit
    cover_letters = db.query(CoverLetter).filter(
        CoverLetter.user_id == user.id
    ).order_by(
        CoverLetter.created_at.desc()
    ).offset(offset).limit(limit).all()

    # 응답 데이터 생성
    data = []
    for cl in cover_letters:
        company = db.query(Company).filter(Company.id == cl.company_id).first()
        job_category = None
        if cl.job_category_id:
            job_category = db.query(JobCategory).filter(
                JobCategory.id == cl.job_category_id
            ).first()

        data.append(CoverLetterListItem(
            id=cl.id,
            company_name=company.name if company else "Unknown",
            job_category_name=job_category.name if job_category else None,
            status=cl.status,
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

    # 권한 확인
    if cover_letter.user_id != user.id:
        raise CoverLetterForbiddenException()

    # 기업 정보
    company = db.query(Company).filter(Company.id == cover_letter.company_id).first()
    company_name = company.name if company else "Unknown"

    # 직군 정보
    job_category_name = None
    if cover_letter.job_category_id:
        job_category = db.query(JobCategory).filter(
            JobCategory.id == cover_letter.job_category_id
        ).first()
        if job_category:
            job_category_name = job_category.name

    # 응답 생성
    cover_letter_response = _build_cover_letter_response(
        cover_letter=cover_letter,
        company_name=company_name,
        job_category_name=job_category_name
    )

    # matching_analysis 추출
    matching_analysis = None
    if cover_letter.generation_metadata:
        matching_analysis = cover_letter.generation_metadata.get("metadata")

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

    # 권한 확인
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
    # items JSONB를 CoverLetterItemResponse 리스트로 변환
    item_responses = []
    items_data = cover_letter.items or []

    for item in items_data:
        question_data = item.get("question", {})
        answer_data = item.get("answer", {})

        item_responses.append(CoverLetterItemResponse(
            question=QuestionResponse(
                content=question_data.get("content", ""),
                min_length=question_data.get("min_length", 500),
                max_length=question_data.get("max_length", 700)
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


def _generate_guide_comments(
    answer_content: str,
    min_length: int,
    max_length: int
) -> List[str]:
    """답변 길이 기반 가이드 코멘트 생성"""
    comments = []
    length = len(answer_content)

    if length < min_length:
        diff = min_length - length
        comments.append(f"답변이 {diff}자 부족합니다. 더 구체적인 내용을 추가해보세요.")
    elif length > max_length:
        diff = length - max_length
        comments.append(f"답변이 {diff}자 초과했습니다. 핵심 내용 위주로 줄여보세요.")

    if length < 300:
        comments.append("프로젝트 기간이나 구체적인 수치를 명시하면 더 설득력이 있습니다.")

    return comments
