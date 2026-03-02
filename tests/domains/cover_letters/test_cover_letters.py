# test_cover_letters.py — 자소서 수정 API 테스트

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.domains.cover_letters.service import update_cover_letter
from app.domains.cover_letters.schemas import CoverLetterUpdateRequest, CoverLetterItemUpdateInput, QuestionInput, AnswerUpdateInput
from app.domains.cover_letters.exceptions import CoverLetterNotFoundException, CoverLetterForbiddenException


class TestUpdateCoverLetterService:
    """자소서 수정 서비스 로직 테스트"""

    @pytest.fixture
    def mock_db(self):
        """Mock DB 세션"""
        return Mock()

    @pytest.fixture
    def mock_user(self):
        """Mock 사용자"""
        user = Mock()
        user.id = 1
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_cover_letter(self):
        """Mock 자소서"""
        from datetime import datetime
        cover_letter = Mock()
        cover_letter.id = 1
        cover_letter.user_id = 1
        cover_letter.company_id = 10
        cover_letter.job_category_id = 5
        cover_letter.created_at = datetime(2024, 1, 1, 12, 0, 0)
        cover_letter.items = [
            {
                "question": {
                    "content": "지원 동기를 작성해주세요",
                    "min_length": 500,
                    "max_length": 700
                },
                "answer": {
                    "content": "원본 답변 내용입니다.",
                    "length": 20,
                    "guide_comments": ["프로젝트 기간을 명시하면 더 구체적입니다"]
                }
            }
        ]
        cover_letter.status = "completed"
        return cover_letter

    @pytest.fixture
    def update_request(self):
        """자소서 수정 요청"""
        return CoverLetterUpdateRequest(
            items=[
                CoverLetterItemUpdateInput(
                    question=QuestionInput(
                        content="지원 동기를 작성해주세요",
                        min_length=500,
                        max_length=700
                    ),
                    answer=AnswerUpdateInput(
                        content="수정된 답변 내용입니다. 더 구체적으로 작성했습니다."
                    )
                )
            ]
        )

    def test_update_cover_letter_success(self, mock_db, mock_user, mock_cover_letter, update_request):
        """정상적인 자소서 수정 - Happy Path"""
        # Mock 설정 - 쿼리 체인 수정
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = mock_cover_letter
        mock_query.filter.return_value = mock_filter
        
        # Mock company와 job_category
        mock_company = Mock()
        mock_company.name = "삼성전자"
        mock_job_category = Mock()
        mock_job_category.name = "소프트웨어 개발"
        
        # 쿼리마다 다른 mock 반환
        def query_side_effect(model):
            new_query = Mock()
            new_filter = Mock()
            if hasattr(model, '__name__'):
                if model.__name__ == 'CoverLetter':
                    new_filter.first.return_value = mock_cover_letter
                elif model.__name__ == 'Company':
                    new_filter.first.return_value = mock_company
                elif model.__name__ == 'JobCategory':
                    new_filter.first.return_value = mock_job_category
            new_query.filter.return_value = new_filter
            return new_query
        
        mock_db.query.side_effect = query_side_effect

        # 테스트 실행
        with patch('app.domains.cover_letters.service.flag_modified'):
            result = update_cover_letter(mock_db, mock_user, 1, update_request)

        # 검증
        assert mock_cover_letter.items[0]["answer"]["content"] == "수정된 답변 내용입니다. 더 구체적으로 작성했습니다."
        assert mock_cover_letter.items[0]["answer"]["length"] == 29  # 한글 문자열 길이
        assert mock_cover_letter.items[0]["answer"]["guide_comments"] == ["프로젝트 기간을 명시하면 더 구체적입니다"]
        mock_db.commit.assert_called_once()

    def test_update_cover_letter_not_found(self, mock_db, mock_user, update_request):
        """존재하지 않는 자소서 수정 시도"""
        # Mock 설정: 자소서 없음
        mock_db.query().filter().first.return_value = None

        # 테스트 실행 및 검증
        with pytest.raises(CoverLetterNotFoundException):
            update_cover_letter(mock_db, mock_user, 99999, update_request)

    def test_update_cover_letter_forbidden(self, mock_db, mock_user, mock_cover_letter, update_request):
        """타인의 자소서 수정 시도 - 권한 없음"""
        # Mock 설정: 소유자가 다름
        mock_cover_letter.user_id = 999
        mock_db.query().filter().first.return_value = mock_cover_letter

        # 테스트 실행 및 검증
        with pytest.raises(CoverLetterForbiddenException):
            update_cover_letter(mock_db, mock_user, 1, update_request)

    def test_update_cover_letter_preserves_guide_comments(self, mock_db, mock_user, mock_cover_letter, update_request):
        """guide_comments 보존 확인"""
        # Mock 설정
        original_guide_comments = ["원본 가이드 코멘트"]
        mock_cover_letter.items[0]["answer"]["guide_comments"] = original_guide_comments
        
        mock_company = Mock()
        mock_company.name = "테스트기업"
        mock_job_category = Mock()
        mock_job_category.name = "테스트직군"
        
        def query_side_effect(model):
            new_query = Mock()
            new_filter = Mock()
            if hasattr(model, '__name__'):
                if model.__name__ == 'CoverLetter':
                    new_filter.first.return_value = mock_cover_letter
                elif model.__name__ == 'Company':
                    new_filter.first.return_value = mock_company
                elif model.__name__ == 'JobCategory':
                    new_filter.first.return_value = mock_job_category
            new_query.filter.return_value = new_filter
            return new_query
        
        mock_db.query.side_effect = query_side_effect

        # 테스트 실행
        with patch('app.domains.cover_letters.service.flag_modified'):
            update_cover_letter(mock_db, mock_user, 1, update_request)

        # guide_comments가 그대로 유지되는지 확인
        assert mock_cover_letter.items[0]["answer"]["guide_comments"] == original_guide_comments

    def test_update_cover_letter_calculates_length(self, mock_db, mock_user, mock_cover_letter, update_request):
        """answer.length 자동 계산 확인"""
        # Mock 설정
        mock_company = Mock()
        mock_company.name = "기업"
        mock_job_category = Mock()
        mock_job_category.name = "직군"
        
        def query_side_effect(model):
            new_query = Mock()
            new_filter = Mock()
            if hasattr(model, '__name__'):
                if model.__name__ == 'CoverLetter':
                    new_filter.first.return_value = mock_cover_letter
                elif model.__name__ == 'Company':
                    new_filter.first.return_value = mock_company
                elif model.__name__ == 'JobCategory':
                    new_filter.first.return_value = mock_job_category
            new_query.filter.return_value = new_filter
            return new_query
        
        mock_db.query.side_effect = query_side_effect

        # 테스트 실행
        with patch('app.domains.cover_letters.service.flag_modified'):
            update_cover_letter(mock_db, mock_user, 1, update_request)

        # length가 자동 계산되었는지 확인
        expected_length = len("수정된 답변 내용입니다. 더 구체적으로 작성했습니다.")
        assert mock_cover_letter.items[0]["answer"]["length"] == expected_length


class TestCoverLetterRouter:
    """자소서 수정 API 라우터 테스트"""

    def test_router_returns_404_on_not_found(self):
        """라우터가 404를 올바르게 반환하는지 확인"""
        from app.domains.cover_letters.router import update_cover_letter_api
        from app.domains.cover_letters.exceptions import CoverLetterNotFoundException
        
        with patch('app.domains.cover_letters.router.update_cover_letter', side_effect=CoverLetterNotFoundException()):
            with pytest.raises(HTTPException) as exc_info:
                update_cover_letter_api(1, Mock(), Mock(), Mock())
            
            assert exc_info.value.status_code == 404
            assert "찾을 수 없습니다" in exc_info.value.detail

    def test_router_returns_403_on_forbidden(self):
        """라우터가 403을 올바르게 반환하는지 확인"""
        from app.domains.cover_letters.router import update_cover_letter_api
        from app.domains.cover_letters.exceptions import CoverLetterForbiddenException
        
        with patch('app.domains.cover_letters.router.update_cover_letter', side_effect=CoverLetterForbiddenException()):
            with pytest.raises(HTTPException) as exc_info:
                update_cover_letter_api(1, Mock(), Mock(), Mock())
            
            assert exc_info.value.status_code == 403
            assert "권한이 없습니다" in exc_info.value.detail

