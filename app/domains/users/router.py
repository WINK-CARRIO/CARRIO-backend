# 회원가입 api 정의 , service.py 이용, schemas.py(요청/응답) 이용
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.shared.database import get_db
from .schemas import UserResponse
from .models import User
# from .service import create_user
from ..auth.schemas import RegisterRequest

router = APIRouter(prefix="/users", tags=["Users"])


