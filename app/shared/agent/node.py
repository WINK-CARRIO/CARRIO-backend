"""
LangGraph 노드 정의
Extraction(추출)과 Generation(생성) 파이프라인의 노드를 분리하여 정의
"""
from typing import Dict, Any, List
from .state import ExtractionState, GenerationState
from .agents import (
    get_researcher, get_scraper, get_analyzer,
    get_strategist, get_writer, get_orchestrator
)

# ==========================================
# 인재상 추출 노드
# ==========================================

async def generate_search_queries_node(state: ExtractionState) -> Dict[str, Any]:
    """검색 쿼리 생성 (ResearcherAgent)"""
    researcher = get_researcher()

    queries = await researcher.generate_search_queries(
        company_name=state["company_name"],
        company_info=state.get("company_info", {}),
        job_category=state.get("job_category")
    )
    return {"search_queries": queries}


async def search_with_tavily_node(state: ExtractionState) -> Dict[str, Any]:
    """Tavily 검색 수행 (ResearcherAgent)"""
    researcher = get_researcher()

    results = await researcher.search_with_tavily(
        queries=state["search_queries"],
        max_results_per_query=3
    )
    return {"search_results": results}


async def extract_urls_node(state: ExtractionState) -> Dict[str, Any]:
    """스크래핑할 URL 추출 (ScraperAgent)"""
    scraper = get_scraper()

    urls = await scraper.extract_urls_to_scrape(
        search_results=state["search_results"],
        max_urls=3
    )
    return {"scraping_urls": urls}


async def scrape_with_firecrawl_node(state: ExtractionState) -> Dict[str, Any]:
    """Firecrawl 스크래핑 수행 (ScraperAgent)"""
    scraper = get_scraper()

    contents = await scraper.scrape_with_firecrawl(urls=state["scraping_urls"])
    return {"scraped_contents": contents}


async def analyze_company_dna_node(state: ExtractionState) -> Dict[str, Any]:
    """기업 DNA 추출 (AnalyzerAgent)"""
    analyzer = get_analyzer()

    company_dna = await analyzer.extract_company_dna(
        company_name=state["company_name"],
        search_results=state["search_results"],
        scraped_contents=state["scraped_contents"],
        job_category=state.get("job_category")
    )
    return {"company_dna": company_dna}


# ==========================================
# 자소서 생성 노드
# ==========================================

async def create_strategy_node(state: GenerationState) -> Dict[str, Any]:
    """매칭 전략 수립 (StrategistAgent)"""
    strategist = get_strategist()

    matching_strategy = await strategist.create_matching_strategy(
        company_name=state["company_info"].get("name", ""),
        company_dna=state["company_dna"],
        user_spec=state["user_spec"],
        questions=state["questions"]
    )
    return {"matching_strategy": matching_strategy}


async def write_single_answer_node(state: dict) -> Dict[str, Any]:
    """단일 질문 답변 생성 (WriterAgent)"""
    writer = get_writer()

    question_info = state["question_info"]
    question_index = state["question_index"]

    generated_answer = await writer.write_single_answer(
        question_info=question_info,
        question_index=question_index,
        company_name=state["company_info"].get("name", ""),
        company_dna=state["company_dna"],
        matching_strategy=state["matching_strategy"],
        user_spec=state["user_spec"]
    )

    return {"answers": [generated_answer]}


async def orchestrate_node(state: GenerationState) -> Dict[str, Any]:
    """최종 조합 및 품질 검증 (OrchestratorAgent)"""
    orchestrator = get_orchestrator()

    result = await orchestrator.orchestrate_and_verify(
        questions=state["questions"],
        answers=state["answers"],
        company_dna=state["company_dna"],
        matching_strategy=state["matching_strategy"]
    )

    return {
        "final_result": result["final_result"],
        "quality_report": result["quality_report"]
    }