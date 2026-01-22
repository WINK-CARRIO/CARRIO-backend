from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.domains.users.models import User
from .schemas import RegisterRequest, UpdateMeRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 회원가입 로직
def hash_password(password: str) -> str:
    print("PASSWORD VALUE:", password)
    print("PASSWORD TYPE:", type(password))
    print("PASSWORD LEN:", len(password))
    print("PASSWORD BYTE LEN:", len(password.encode("utf-8")))

    return pwd_context.hash(password)



def create_user(db: Session, user_create: RegisterRequest) -> User:
    hashed_password = hash_password(user_create.password)

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



def authenticate_user(db: Session, email: str, password: str) -> User | None:
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
def delete_me(db: Session, user: User, password: str | None):
    if user.oauth_provider == "email":
        if not password:
            raise HTTPException(
                status_code=400,
                detail="비밀번호가 필요합니다",
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="비밀번호가 올바르지 않습니다",
            )

    db.delete(user)
    db.commit()