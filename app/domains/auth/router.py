from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from app.shared.database import get_db
from app.domains.users.models import User
from app.domains.users.schemas import UserResponse
from .kakao import get_kakao_user
from .schemas import RegisterRequest, LoginRequest, AuthResponse, UpdateMeRequest, DeleteMeRequest
from .service import create_user, authenticate_user, update_me, delete_me, get_or_create_kakao_user
from .jwt import create_access_token
from .dependencies import get_current_user
from ...config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    user = create_user(db, body)
    access_token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/login", response_model=AuthResponse)
def login(
        body: LoginRequest,
        db: Session = Depends(get_db),
):
    user = authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_my_info(
        body: UpdateMeRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return update_me(db, current_user, body)

@router.delete("/me", status_code=204)
def delete_me_api(
        body: DeleteMeRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    delete_me(db, current_user, body.password)


@router.get("/kakao/login")
def kakao_login():
    kakao_auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        "?response_type=code"
        f"&client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
    )
    return {"url": kakao_auth_url}

@router.get("/kakao/callback")
async def kakao_callback(code: str, db: Session = Depends(get_db)):

    kakao_user = await get_kakao_user(code)
    user = get_or_create_kakao_user(db, kakao_user)
    access_token = create_access_token({"sub": str(user.id)})

    redirect_url = f"http://localhost:5173/kakao/callback?token={access_token}"

    return RedirectResponse(url=redirect_url)

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {
        "message": "Logout successful. Please delete token on client."
    }
