# test_auth.py — Auth 도메인 스키마 + 라우터 테스트

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from fastapi import HTTPException

from app.domains.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
)
from app.domains.users.schemas import UserResponse


class TestAuthSchemas:
    """Auth 스키마 검증 테스트"""

    def test_login_request_valid(self):
        """LoginRequest 정상 생성"""
        req = LoginRequest(email="test@example.com", password="password123")
        assert req.email == "test@example.com"
        assert req.password == "password123"

    def test_login_request_invalid_email(self):
        """LoginRequest 이메일 형식 검증"""
        with pytest.raises(Exception):
            LoginRequest(email="not-an-email", password="password123")

    def test_auth_response_structure(self):
        """AuthResponse에 token + user 포함 확인"""
        user = UserResponse(
            id=1,
            email="test@example.com",
            name="Test",
            role="user",
            oauth_provider="email",
            created_at=datetime(2026, 1, 1),
        )
        resp = AuthResponse(
            access_token="jwt-token-here",
            token_type="bearer",
            user=user,
        )
        assert resp.access_token == "jwt-token-here"
        assert resp.token_type == "bearer"
        assert resp.user.id == 1
        assert resp.user.oauth_provider == "email"
        assert resp.user.created_at == datetime(2026, 1, 1)

    def test_register_request_password_min_length(self):
        """RegisterRequest 비밀번호 8자 미만 거부"""
        with pytest.raises(Exception):
            RegisterRequest(email="a@b.com", password="short", name="Test")

    def test_register_request_password_valid(self):
        """RegisterRequest 비밀번호 8자 이상 통과"""
        req = RegisterRequest(email="a@b.com", password="validpass", name="Test")
        assert req.password == "validpass"


class TestUserResponseSchema:
    """UserResponse 스키마 검증 테스트"""

    def test_user_response_includes_oauth_provider(self):
        """UserResponse에 oauth_provider 필드 포함"""
        user = UserResponse(
            id=1,
            email="test@example.com",
            name="Test",
            role="user",
            oauth_provider="kakao",
            created_at=datetime(2026, 2, 10),
        )
        assert user.oauth_provider == "kakao"

    def test_user_response_includes_created_at(self):
        """UserResponse에 created_at 필드 포함"""
        dt = datetime(2026, 2, 10, 12, 0, 0)
        user = UserResponse(
            id=1,
            email="test@example.com",
            name="Test",
            role="user",
            oauth_provider="email",
            created_at=dt,
        )
        assert user.created_at == dt

    def test_user_response_from_orm(self):
        """UserResponse ORM 객체 변환 테스트"""
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.name = "Test"
        mock_user.role = "user"
        mock_user.oauth_provider = "email"
        mock_user.created_at = datetime(2026, 1, 1)

        user = UserResponse.model_validate(mock_user, from_attributes=True)
        assert user.id == 1
        assert user.oauth_provider == "email"
        assert user.created_at == datetime(2026, 1, 1)


class TestAuthRouter:
    """Auth 라우터 테스트"""

    def test_register_returns_auth_response_with_token(self):
        """register가 AuthResponse(token + user) 반환"""
        from app.domains.auth.router import register

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "new@example.com"
        mock_user.name = "New User"
        mock_user.role = "user"
        mock_user.oauth_provider = "email"
        mock_user.created_at = datetime(2026, 3, 1)

        body = RegisterRequest(email="new@example.com", password="password123", name="New User")

        with patch("app.domains.auth.router.create_user", return_value=mock_user):
            with patch("app.domains.auth.router.create_access_token", return_value="test-jwt-token"):
                result = register(body, mock_db)

        assert result["access_token"] == "test-jwt-token"
        assert result["token_type"] == "bearer"
        assert result["user"] == mock_user

    def test_login_success_returns_auth_response(self):
        """login 성공 시 AuthResponse 반환"""
        from app.domains.auth.router import login

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "user@example.com"
        mock_user.name = "User"
        mock_user.role = "user"
        mock_user.oauth_provider = "email"
        mock_user.created_at = datetime(2026, 1, 1)

        body = LoginRequest(email="user@example.com", password="password123")

        with patch("app.domains.auth.router.authenticate_user", return_value=mock_user):
            with patch("app.domains.auth.router.create_access_token", return_value="login-jwt"):
                result = login(body, mock_db)

        assert result["access_token"] == "login-jwt"
        assert result["user"] == mock_user

    def test_login_failure_raises_401(self):
        """login 실패 시 401 반환"""
        from app.domains.auth.router import login

        mock_db = Mock()
        body = LoginRequest(email="wrong@example.com", password="wrongpass")

        with patch("app.domains.auth.router.authenticate_user", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                login(body, mock_db)

        assert exc_info.value.status_code == 401

    def test_login_accepts_json_body_not_form_data(self):
        """login이 LoginRequest(JSON body)를 받는지 확인"""
        from app.domains.auth.router import login
        import inspect

        sig = inspect.signature(login)
        params = list(sig.parameters.keys())

        # 'body' 파라미터가 있어야 함 (form이 아님)
        assert "body" in params
        assert "form" not in params
