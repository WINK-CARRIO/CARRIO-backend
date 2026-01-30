from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status

from .exceptions import (
    EmailAlreadyExistsError,
    PasswordRequiredError,
    InvalidPasswordError,
)

def register_auth_exception_handlers(app):
    @app.exception_handler(EmailAlreadyExistsError)
    async def email_exists_handler(
            request: Request,
            exc: EmailAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "이미 존재하는 이메일입니다."},
        )

    @app.exception_handler(PasswordRequiredError)
    async def password_required_handler(
            request: Request,
            exc: PasswordRequiredError,
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "비밀번호가 필요합니다."},
        )

    @app.exception_handler(InvalidPasswordError)
    async def invalid_password_handler(
            request: Request,
            exc: InvalidPasswordError,
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "비밀번호가 올바르지 않습니다."},
        )