#회원가입/로그인 요청, 토근 응답
from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UpdateMeRequest(BaseModel):
    name: Optional[str] = None

class DeleteMeRequest(BaseModel):
    password: Optional[str] = None