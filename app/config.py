from pydantic_settings import BaseSettings
from typing import ClassVar, List
from typing import Optional

class Settings(BaseSettings):
    """환경 설정"""
    # Database
    DATABASE_URL: str
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Kakao OAuth (Optional for development)
    KAKAO_CLIENT_ID: Optional[str] = "dev-client-id" #TODO 하드코딩됨 추후 변경
    KAKAO_CLIENT_SECRET: Optional[str] = "dev-client-secret" #TODO 하드코딩됨 추후 변경

    # 초기 관리자
    INITIAL_ADMIN_EMAILS: List[str] = []

    # 프론트 url
    FRONTEND_URL: str

# JWT
    SECRET_KEY: Optional[str] = "dev-secret-key-change-in-production" #TODO 하드코딩됨 추후 변경
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24시간
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 추가 환경 변수 허용 TODO ignore로 추후 변경

settings = Settings()
