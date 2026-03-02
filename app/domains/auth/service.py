from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional
from app.domains.users.models import User
from .exceptions import EmailAlreadyExistsError, PasswordRequiredError, InvalidPasswordError
from .schemas import RegisterRequest, UpdateMeRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 회원가입 로직
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_user(db: Session, user_create: RegisterRequest) -> User:
    # 해싱
    hashed_password = hash_password(user_create.password)

    # 이메일 중복 방지 로직
    existing_user = (
        db.query(User)
        .filter(User.email == user_create.email)
        .first()
    )
    if existing_user:
        raise EmailAlreadyExistsError()

    # 필드 매핑
    user = User(
        email=user_create.email,
        password_hash=hashed_password,
        name=user_create.name,
        oauth_provider="email",
        role="user",
    )

    db.add(user)  # 이 객체를 db에 저장하겠다고 예약
    db.commit()   # 실제 db에 반영
    db.refresh(user)   # db 최신화 (db 다시조회해서 자동 생성 컬을 채움)

    return user

# 로그인 로직
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

# 회원 name 수정
def update_me(db: Session, user: User, body: UpdateMeRequest) -> User:
    if body.name is not None:
        user.name = body.name

    db.commit()
    db.refresh(user)
    return user

#회원 탈퇴
def delete_me(db: Session, user: User, password: Optional[str]):
    if user.oauth_provider == "email":
        if not password:
            raise PasswordRequiredError()
        if not verify_password(password, user.password_hash):
            raise InvalidPasswordError()

    db.delete(user)
    db.commit()

# 카카오 유저 처리
def get_or_create_kakao_user(db: Session, kakao_user: dict) -> User:
    # 1. 이미 카카오로 가입된 유저인지 확인
    user = (
        db.query(User)
        .filter(
            User.oauth_provider == "kakao",
            User.oauth_id == kakao_user["oauth_id"]
        )
        .first()
    )
    if user:
        return user

    # 2. 이메일 중복 체크 (일반 회원과 충돌 방지)
    if kakao_user.get("email"):
        existing_user = (
            db.query(User)
            .filter(User.email == kakao_user["email"])
            .first()
        )
        if existing_user:
            raise EmailAlreadyExistsError()

    # 3.신규 카카오 유저 생성
    user = User(
        email=kakao_user["email"],
        name=kakao_user["name"],
        oauth_provider="kakao",
        oauth_id=kakao_user["oauth_id"],
        role="user",
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user