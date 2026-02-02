"""
LangGraph 파이프라인 정의
전체 자소서 생성 워크플로우를 그래프로 구성
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from .state import CoverLetterState
from .node import (
    load_user_spec_node,
    load_company_info_node,
    generate_search_queries_node,
    search_with_tavily_node,
    extract_urls_node,
    scrape_with_firecrawl_node,
    analyze_company_dna_node,
    create_strategy_node,
    write_answers_node,
    orchestrate_node
)


def create_cover_letter_graph(db: Session):
    """ 자소서 생성 그래프 생성 """
    # StateGraph 생성
    workflow = StateGraph(CoverLetterState)

    # db를 사용하는 노드를 위한 async wrapper
    async def load_user_spec_wrapper(state):
        return await load_user_spec_node(state, db)

    async def load_company_info_wrapper(state):
        return await load_company_info_node(state, db)

    # ===== 노드 추가 =====

    # Stage 1: 데이터 수집
    workflow.add_node("load_user_spec", load_user_spec_wrapper)
    workflow.add_node("load_company_info", load_company_info_wrapper)
    workflow.add_node("generate_search_queries", generate_search_queries_node)
    workflow.add_node("search_with_tavily", search_with_tavily_node)
    workflow.add_node("extract_urls", extract_urls_node)
    workflow.add_node("scrape_with_firecrawl", scrape_with_firecrawl_node)

    # Stage 2: 분석 및 전략 수립
    workflow.add_node("analyze_company_dna", analyze_company_dna_node)
    workflow.add_node("create_strategy", create_strategy_node)

    # Stage 3: 답변 생성 (단일 노드, 내부에서 asyncio.gather로 병렬 처리)
    workflow.add_node("write_answers", write_answers_node)

    # Stage 4: 최종 조합 & 품질 검증
    workflow.add_node("orchestrate", orchestrate_node)

    # ===== 엣지 연결 (실행 순서 정의) =====

    # 시작점: load_user_spec
    workflow.set_entry_point("load_user_spec")

    # Stage 1: 데이터 수집 (순차적 실행)
    workflow.add_edge("load_user_spec", "load_company_info")
    workflow.add_edge("load_company_info", "generate_search_queries")
    workflow.add_edge("generate_search_queries", "search_with_tavily")
    workflow.add_edge("search_with_tavily", "extract_urls")
    workflow.add_edge("extract_urls", "scrape_with_firecrawl")

    # Stage 2: 분석 및 전략 수립 (순차적 실행)
    workflow.add_edge("scrape_with_firecrawl", "analyze_company_dna")
    workflow.add_edge("analyze_company_dna", "create_strategy")

    # Stage 3: 답변 생성 (동적 개수의 질문을 내부에서 병렬 처리)
    workflow.add_edge("create_strategy", "write_answers")

    # Stage 4: 최종 조합 & 품질 검증
    workflow.add_edge("write_answers", "orchestrate")

    # 종료
    workflow.add_edge("orchestrate", END)

    # 그래프 컴파일
    return workflow.compile()


async def run_cover_letter_pipeline(
    user_id: int,
    company_id: int,
    job_category_id: int,
    questions: list[str],
    db: Session
) -> Dict[str, Any]:
    """ 자소서 생성 파이프라인 실행 """

    # 초기 상태 생성
    initial_state: CoverLetterState = {
        "user_id": user_id,
        "company_id": company_id,
        "job_category_id": job_category_id,
        "questions": questions,

        # Stage 1
        "user_spec": None,
        "company_info": None,
        "search_queries": [],
        "search_results": [],
        "scraping_urls": [],
        "scraped_contents": [],

        # Stage 2
        "company_dna": None,
        "matching_strategy": None,

        # Stage 3
        "answers": [],

        # Stage 4
        "final_cover_letter": None,
        "quality_report": None,

        # 메타데이터
        "generation_metadata": {},
        "status": "pending",
        "error": None
    }

    # 그래프 생성
    graph = create_cover_letter_graph(db)

    # 그래프 실행
    try:
        final_state = await graph.ainvoke(initial_state)

        # 성공 시 상태 업데이트
        final_state["status"] = "completed"

        return {
            "final_cover_letter": final_state.get("final_cover_letter"),
            "quality_report": final_state.get("quality_report"),
            "generation_metadata": final_state.get("generation_metadata", {}),
            "status": final_state.get("status"),
        }

    except Exception as e:
        # 실패 시 에러 정보 반환
        return {
            "final_cover_letter": None,
            "quality_report": None,
            "generation_metadata": {},
            "status": "failed",
            "error": str(e)
        }