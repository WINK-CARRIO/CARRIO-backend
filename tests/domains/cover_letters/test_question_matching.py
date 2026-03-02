# test_question_matching.py
# _save_cover_letter_result의 question 매칭 로직 테스트
#
# 배경:
#   Orchestrator LLM이 final_items을 반환할 때, 각 항목에 question_index(1-based)가 포함됨.
#   저장 시 question_index로 1순위 매칭하고, 없으면 텍스트로 fallback한다.

import pytest
from unittest.mock import Mock, patch
from app.domains.cover_letters.service import _save_cover_letter_result
from app.domains.cover_letters.schemas import CoverLetterCreateRequest, QuestionInput


@pytest.fixture
def mock_db():
    db = Mock()
    db.refresh = Mock()  # refresh는 아무것도 안 해도 됨
    return db


@pytest.fixture
def mock_user():
    user = Mock()
    user.id = 1
    return user


@pytest.fixture
def three_question_request():
    """질문 3개짜리 자소서 생성 요청"""
    return CoverLetterCreateRequest(
        company_id=1,
        questions=[
            QuestionInput(content="지원 동기를 작성하세요", min_length=300, max_length=500),
            QuestionInput(content="본인의 강점을 작성하세요", min_length=300, max_length=500),
            QuestionInput(content="입사 후 목표를 작성하세요", min_length=300, max_length=500),
        ]
    )


class TestQuestionIndexMatching:
    """question_index 기반 매칭 (1순위)"""

    def test_index_matching_success(self, mock_db, mock_user, three_question_request):
        """question_index로 정확히 매칭되면 올바른 답변이 저장된다"""
        # Orchestrator가 question 텍스트를 살짝 바꿔서 반환한 상황
        result = {
            "final_result": [
                {"question_index": 1, "question": "지원 동기", "answer": "삼성을 지원한 이유는...", "guide_comments": ["구체적인 수치 추가 필요"]},
                {"question_index": 2, "question": "강점 소개", "answer": "제 강점은...", "guide_comments": []},
                {"question_index": 3, "question": "목표 서술", "answer": "입사 후 5년 안에...", "guide_comments": []},
            ],
            "quality_report": {"overall_score": 85},
            "status": "completed"
        }

        with patch("app.domains.cover_letters.service.CoverLetter") as MockCoverLetter:
            mock_instance = Mock()
            mock_instance.id = 1
            mock_instance.user_id = 1
            mock_instance.company_id = 1
            mock_instance.job_category_id = None
            mock_instance.items = []
            mock_instance.status = "completed"
            mock_instance.generation_metadata = {}
            MockCoverLetter.return_value = mock_instance

            _save_cover_letter_result(
                db=mock_db,
                user=mock_user,
                user_spec_id=1,
                request=three_question_request,
                result=result
            )

            items_saved = MockCoverLetter.call_args.kwargs["items"]

        assert len(items_saved) == 3
        # question_index=1 → 첫 번째 질문에 "삼성을 지원한 이유는..." 매칭
        assert items_saved[0]["answer"]["content"] == "삼성을 지원한 이유는..."
        assert items_saved[1]["answer"]["content"] == "제 강점은..."
        assert items_saved[2]["answer"]["content"] == "입사 후 5년 안에..."

    def test_index_matching_ignores_text_change(self, mock_db, mock_user, three_question_request):
        """LLM이 question 텍스트를 바꿔도 index로 정확히 찾는다"""
        result = {
            "final_result": [
                # question 텍스트가 원본과 완전히 다름
                {"question_index": 2, "question": "전혀 다른 텍스트", "answer": "강점 답변", "guide_comments": []},
                {"question_index": 1, "question": "또 다른 텍스트", "answer": "동기 답변", "guide_comments": []},
                {"question_index": 3, "question": "역시 다른 텍스트", "answer": "목표 답변", "guide_comments": []},
            ],
            "quality_report": {},
            "status": "completed"
        }

        with patch("app.domains.cover_letters.service.CoverLetter") as MockCoverLetter:
            mock_instance = Mock()
            mock_instance.id = 1
            mock_instance.user_id = 1
            mock_instance.company_id = 1
            mock_instance.job_category_id = None
            mock_instance.items = []
            mock_instance.status = "completed"
            mock_instance.generation_metadata = {}
            MockCoverLetter.return_value = mock_instance

            _save_cover_letter_result(
                db=mock_db,
                user=mock_user,
                user_spec_id=1,
                request=three_question_request,
                result=result
            )

            items_saved = MockCoverLetter.call_args.kwargs["items"]

        # index 기반이므로 question_index=1 → 첫 번째 질문, question_index=2 → 두 번째 질문
        assert items_saved[0]["answer"]["content"] == "동기 답변"
        assert items_saved[1]["answer"]["content"] == "강점 답변"
        assert items_saved[2]["answer"]["content"] == "목표 답변"


class TestTextFallbackMatching:
    """question_index 없을 때 텍스트 fallback (2순위)"""

    def test_text_fallback_when_no_index(self, mock_db, mock_user, three_question_request):
        """question_index가 없으면 텍스트로 fallback 매칭한다"""
        result = {
            "final_result": [
                # question_index 없음 — 구버전 LLM 응답 또는 예외 상황
                {"question": "입사 후 목표를 작성하세요", "answer": "목표 답변", "guide_comments": []},
                {"question": "지원 동기를 작성하세요", "answer": "동기 답변", "guide_comments": []},
                {"question": "본인의 강점을 작성하세요", "answer": "강점 답변", "guide_comments": []},
            ],
            "quality_report": {},
            "status": "completed"
        }

        with patch("app.domains.cover_letters.service.CoverLetter") as MockCoverLetter:
            mock_instance = Mock()
            mock_instance.id = 1
            mock_instance.user_id = 1
            mock_instance.company_id = 1
            mock_instance.job_category_id = None
            mock_instance.items = []
            mock_instance.status = "completed"
            mock_instance.generation_metadata = {}
            MockCoverLetter.return_value = mock_instance

            _save_cover_letter_result(
                db=mock_db,
                user=mock_user,
                user_spec_id=1,
                request=three_question_request,
                result=result
            )

            items_saved = MockCoverLetter.call_args.kwargs["items"]

        assert items_saved[0]["answer"]["content"] == "동기 답변"
        assert items_saved[1]["answer"]["content"] == "강점 답변"
        assert items_saved[2]["answer"]["content"] == "목표 답변"


class TestNoMatchFallback:
    """index도 텍스트도 안 맞으면 빈 답변 저장"""

    def test_empty_answer_when_no_match(self, mock_db, mock_user):
        """아무것도 매칭 안 되면 content="" guide_comments=["생성 실패"]로 저장된다"""
        request = CoverLetterCreateRequest(
            company_id=1,
            questions=[QuestionInput(content="지원 동기를 작성하세요")]
        )
        result = {
            # question_index=99(없는 번호), 텍스트도 다름
            "final_result": [
                {"question_index": 99, "question": "전혀 관계없는 질문", "answer": "어떤 답변", "guide_comments": []}
            ],
            "quality_report": {},
            "status": "completed"
        }

        with patch("app.domains.cover_letters.service.CoverLetter") as MockCoverLetter:
            mock_instance = Mock()
            mock_instance.id = 1
            mock_instance.user_id = 1
            mock_instance.company_id = 1
            mock_instance.job_category_id = None
            mock_instance.items = []
            mock_instance.status = "completed"
            mock_instance.generation_metadata = {}
            MockCoverLetter.return_value = mock_instance

            _save_cover_letter_result(
                db=mock_db,
                user=Mock(id=1),
                user_spec_id=1,
                request=request,
                result=result
            )

            items_saved = MockCoverLetter.call_args.kwargs["items"]

        assert items_saved[0]["answer"]["content"] == ""
        assert items_saved[0]["answer"]["guide_comments"] == ["생성 실패"]
