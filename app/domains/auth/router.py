from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session
from app.shared.database import get_db
from app.domains.users.models import User
from app.domains.users.schemas import UserResponse
from .exceptions import EmailAlreadyExistsError
from .schemas import RegisterRequest, TokenResponse, UpdateMeRequest, DeleteMeRequest
from .service import create_user, authenticate_user, update_me, delete_me
from .jwt import create_access_token
from .dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return create_user(db, body)
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )


@router.post("/login", response_model=TokenResponse)
def login(
        form: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
):
    user = authenticate_user(db, form.username, form.password)
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

@router.delete("/me")
def delete_my_account(
        body: DeleteMeRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    delete_me(db, current_user, body.password)
    return {"message": "회원 탈퇴가 완료되었습니다"}