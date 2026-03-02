"""
AI 에이전트 설정
"""
from pydantic_settings import BaseSettings
from typing import Optional

from dotenv import load_dotenv
import os

load_dotenv()  # env 못 읽을 시 주석 제거하고 해보기

class AgentSettings(BaseSettings):
    """AI 에이전트 관련 설정"""

    # API 키
    OPENAI_API_KEY: str

    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MAX_TOKENS: int = 8192

    TAVILY_API_KEY: Optional[str] = None
    FIRECRAWL_API_KEY: Optional[str] = None

    # 모델 설정
    GPT_MODEL: str = "gpt-5.1"   # 변경 가능 (https://developers.openai.com/api/docs/models 참고)
    GPT_MINI_MODEL: str = "gpt-4o-mini"
    CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"  # 변경 가능 (https://platform.claude.com/docs/en/about-claude/models/overview 참고)

    # 검색 설정
    TAVILY_MAX_RESULTS: int = 5
    TAVILY_SEARCH_DEPTH: str = "advanced"  # "basic" or "advanced"

    # 스크래핑 설정
    SCRAPE_MAX_CHARS: int = 10000
    SCRAPE_TIMEOUT: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


agent_settings = AgentSettings()