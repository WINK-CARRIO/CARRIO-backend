from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("비밀번호는 최소 8자 이상이어야 합니다")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UpdateMeRequest(BaseModel):
    name: Optional[str] = None

class DeleteMeRequest(BaseModel):
    password: Optional[str] = None