# test_job_categories.py — 직군 API 스키마 + 라우터 테스트

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from fastapi import HTTPException

from app.domains.job_categories.schemas import (
    JobCategoryResponse,
    JobCategoryListResponse,
)


class TestJobCategorySchemas:
    """직군 스키마 테스트"""

    def test_list_response_wraps_categories(self):
        """JobCategoryListResponse가 job_categories 키로 래핑"""
        categories = [
            JobCategoryResponse(
                id=1, name="백엔드", description="서버 개발",
                created_at=datetime(2026, 1, 1),
            ),
            JobCategoryResponse(
                id=2, name="프론트엔드", description="UI 개발",
                created_at=datetime(2026, 1, 2),
            ),
        ]
        resp = JobCategoryListResponse(job_categories=categories)
        assert len(resp.job_categories) == 2
        assert resp.job_categories[0].name == "백엔드"

    def test_list_response_empty(self):
        """빈 직군 목록도 정상 래핑"""
        resp = JobCategoryListResponse(job_categories=[])
        assert resp.job_categories == []


class TestJobCategoryRouter:
    """직군 라우터 테스트"""

    def test_list_all_no_auth_required(self):
        """GET /job-categories에 인증 의존성 없음"""
        from app.domains.job_categories.router import list_all
        import inspect

        sig = inspect.signature(list_all)
        params = list(sig.parameters.keys())

        # db만 있고 current_user 없어야 함
        assert "db" in params
        assert "current_user" not in params

    def test_list_all_returns_wrapped_response(self):
        """list_all이 {job_categories: [...]} 형태로 반환"""
        from app.domains.job_categories.router import list_all

        mock_db = Mock()
        mock_category = Mock()
        mock_category.id = 1
        mock_category.name = "백엔드"
        mock_category.description = None
        mock_category.created_at = datetime(2026, 1, 1)

        with patch("app.domains.job_categories.router.get_job_categories", return_value=[mock_category]):
            result = list_all(mock_db)

        assert "job_categories" in result
        assert len(result["job_categories"]) == 1

    def test_list_all_empty_returns_empty_list(self):
        """직군 없을 때 빈 배열 래핑 반환"""
        from app.domains.job_categories.router import list_all

        mock_db = Mock()

        with patch("app.domains.job_categories.router.get_job_categories", return_value=[]):
            result = list_all(mock_db)

        assert result == {"job_categories": []}
