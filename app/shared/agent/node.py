"""
LangGraph 노드 정의
각 Stage의 노드들을 정의
"""
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.domains.users.models import UserSpec
from app.domains.companies.models import Company
from .state import CoverLetterState
from .agents import (
    ResearcherAgent,
    ScraperAgent,
    AnalyzerAgent,
    StrategistAgent,
    WriterAgent,
    OrchestratorAgent
)


# ===== Stage 1: 데이터 수집 =====

async def load_user_spec_node(state: CoverLetterState, db: Session) -> Dict[str, Any]:
    """사용자 스펙 로드"""
    user_id = state["user_id"]
    user_spec = db.query(UserSpec).filter(UserSpec.user_id == user_id).first()

    if not user_spec:
        return {"error": "사용자 스펙을 찾을 수 없습니다."}

    spec_data = {
        "structured_data": user_spec.structured_data,
        "free_experiences": user_spec.free_experiences,
    }

    return {"user_spec": spec_data}


async def load_company_info_node(state: CoverLetterState, db: Session) -> Dict[str, Any]:
    """기업 정보 로드"""
    company_id = state["company_id"]
    company = db.query(Company).filter(Company.id == company_id).first()

    if not company:
        return {"error": "기업 정보를 찾을 수 없습니다."}

    company_data = {
        "name": company.name,
        "industry": company.industry,
        "description": company.description,
        "website_url": company.website_url,
    }

    return {"company_info": company_data}


async def generate_search_queries_node(state: CoverLetterState) -> Dict[str, Any]:
    """검색 쿼리 생성 (ResearcherAgent)"""
    researcher = ResearcherAgent()

    company_info = state.get("company_info", {})
    company_name = company_info.get("name", "")
    job_category = None  # TODO: job_category_id로 조회

    queries = await researcher.generate_search_queries(
        company_name=company_name,
        company_info=company_info,
        job_category=job_category
    )

    return {"search_queries": queries}


async def search_with_tavily_node(state: CoverLetterState) -> Dict[str, Any]:
    """Tavily 검색 수행 (ResearcherAgent)"""
    researcher = ResearcherAgent()

    queries = state.get("search_queries", [])

    results = await researcher.search_with_tavily(
        queries=queries,
        max_results_per_query=3
    )

    return {"search_results": results}


async def extract_urls_node(state: CoverLetterState) -> Dict[str, Any]:
    """스크래핑할 URL 추출 (ScraperAgent)"""
    scraper = ScraperAgent()

    search_results = state.get("search_results", [])

    urls = await scraper.extract_urls_to_scrape(
        search_results=search_results,
        max_urls=5
    )

    return {"scraping_urls": urls}


async def scrape_with_firecrawl_node(state: CoverLetterState) -> Dict[str, Any]:
    """Firecrawl 스크래핑 수행 (ScraperAgent)"""
    scraper = ScraperAgent()

    urls = state.get("scraping_urls", [])

    contents = await scraper.scrape_with_firecrawl(urls=urls)

    return {"scraped_contents": contents}


# ===== Stage 2: 분석 및 전략 수립 =====

async def analyze_company_dna_node(state: CoverLetterState) -> Dict[str, Any]:
    """기업 DNA 추출 (AnalyzerAgent)"""
    analyzer = AnalyzerAgent()

    company_info = state.get("company_info", {})
    company_name = company_info.get("name", "")
    search_results = state.get("search_results", [])
    scraped_contents = state.get("scraped_contents", [])

    company_dna = await analyzer.extract_company_dna(
        company_name=company_name,
        search_results=search_results,
        scraped_contents=scraped_contents
    )

    return {"company_dna": company_dna}


async def create_strategy_node(state: CoverLetterState) -> Dict[str, Any]:
    """매칭 전략 수립 (StrategistAgent)"""
    strategist = StrategistAgent()

    company_info = state.get("company_info", {})
    company_name = company_info.get("name", "")
    company_dna = state.get("company_dna")
    user_spec = state.get("user_spec", {})
    questions = state.get("questions", [])

    matching_strategy = await strategist.create_matching_strategy(
        company_name=company_name,
        company_dna=company_dna,
        user_spec=user_spec,
        questions=questions
    )

    return {"matching_strategy": matching_strategy}


# ===== Stage 3: 답변 생성 (병렬) =====

async def write_answers_node(state: CoverLetterState) -> Dict[str, Any]:
    """
    모든 질문에 대한 답변을 병렬로 작성 (WriterAgent)
    질문 개수에 관계없이 동적으로 처리
    """
    writer = WriterAgent()

    company_info = state.get("company_info", {})
    questions = state.get("questions", [])
    company_name = company_info.get("name", "")
    company_dna = state.get("company_dna")
    matching_strategy = state.get("matching_strategy")
    user_spec = state.get("user_spec", {})

    # 모든 질문에 대해 병렬로 답변 생성
    tasks = [
        writer.write_single_answer(
            question=question,
            company_name=company_name,
            company_dna=company_dna,
            matching_strategy=matching_strategy,
            user_spec=user_spec
        )
        for question in questions
    ]

    answers: List[str] = await asyncio.gather(*tasks)

    return {"answers": answers}


# ===== Stage 4: 최종 조합 & 품질 검증 =====

async def orchestrate_node(state: CoverLetterState) -> Dict[str, Any]:
    """최종 조합 및 품질 검증 (OrchestratorAgent)"""
    orchestrator = OrchestratorAgent()

    questions = state.get("questions", [])
    answers = state.get("answers", [])
    company_dna = state.get("company_dna")
    matching_strategy = state.get("matching_strategy")

    result = await orchestrator.orchestrate_and_verify(
        questions=questions,
        answers=answers,
        company_dna=company_dna,
        matching_strategy=matching_strategy
    )

    return {
        "final_cover_letter": result["final_cover_letter"],
        "quality_report": result["quality_report"]
    }
