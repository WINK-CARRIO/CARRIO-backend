"""
LangGraph 파이프라인 정의
"""
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.constants import Send
from langgraph.types import RetryPolicy

from .state import ExtractionState, GenerationState
from .node import (
    generate_search_queries_node,
    search_with_tavily_node,
    extract_urls_node,
    scrape_with_firecrawl_node,
    analyze_company_dna_node,
    create_strategy_node,
    write_single_answer_node,
    orchestrate_node
)


# ==========================================
# 인재상 추출용
# ==========================================

def create_extraction_graph():
    """인재상 추출 파이프라인 그래프 생성"""
    workflow = StateGraph(ExtractionState)

    retry_policy = RetryPolicy(max_attempts=3)

    workflow.add_node("generate_queries", generate_search_queries_node, retry=retry_policy)
    workflow.add_node("search", search_with_tavily_node, retry=retry_policy)
    workflow.add_node("extract_urls", extract_urls_node, retry=retry_policy)

    workflow.add_node("scrape", scrape_with_firecrawl_node, retry=RetryPolicy(max_attempts=2))

    workflow.add_node("analyze", analyze_company_dna_node, retry=retry_policy)

    workflow.set_entry_point("generate_queries")
    workflow.add_edge("generate_queries", "search")
    workflow.add_edge("search", "extract_urls")
    workflow.add_edge("extract_urls", "scrape")
    workflow.add_edge("scrape", "analyze")
    workflow.add_edge("analyze", END)

    return workflow.compile()


async def run_extraction_pipeline(
    company_name: str,
    company_info: Dict[str, Any] = None,
    job_category: str = None
) -> Dict[str, Any]:
    """인재상 추출 파이프라인 실행"""

    initial_state = {
        "company_name": company_name,
        "company_info": company_info or {},
        "job_category": job_category,

        "search_queries": [],
        "search_results": [],
        "scraping_urls": [],
        "scraped_contents": [],

        "company_dna": None,
        "status": "pending",
        "error": None
    }

    graph = create_extraction_graph()

    try:
        result = await graph.ainvoke(initial_state)
        return result.get("company_dna")
    except Exception as e:
        print(f"추출 중 에러: {e}")
        raise e


# ==========================================
# 자소서 생성용
# ==========================================

def map_questions(state: GenerationState):
    """개별 작성 노드로 분배"""
    questions = state.get("questions", [])

    return [
        Send("write_single_answer", {
            "question_info": q,
            "question_index": i,
            "company_info": state["company_info"],
            "matching_strategy": state["matching_strategy"],
            "company_dna": state["company_dna"],
            "user_spec": state["user_spec"]
        })
        for i, q in enumerate(questions)
    ]


def create_generation_graph():
    """자소서 생성 파이프라인 그래프 생성"""
    workflow = StateGraph(GenerationState)

    retry_policy = RetryPolicy(max_attempts=3)

    workflow.add_node("create_strategy", create_strategy_node, retry=retry_policy)
    workflow.add_node("write_single_answer", write_single_answer_node, retry=retry_policy)
    workflow.add_node("orchestrate", orchestrate_node, retry=retry_policy)

    workflow.set_entry_point("create_strategy")

    workflow.add_conditional_edges(
        "create_strategy",
        map_questions,
        ["write_single_answer"]
    )

    workflow.add_edge("write_single_answer", "orchestrate")
    workflow.add_edge("orchestrate", END)

    return workflow.compile()


async def run_generation_pipeline(
    user_spec: Dict[str, Any],
    company_dna: Dict[str, Any],
    company_info: Dict[str, Any],
    questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """자소서 생성 파이프라인 실행"""

    formatted_questions = []
    for i, q in enumerate(questions):
        formatted_questions.append({
            "id": i + 1,
            "content": q["content"],
            "min_length": q.get("min_length"),
            "max_length": q.get("max_length")
        })

    initial_state = {
        "user_spec": user_spec,
        "company_dna": company_dna,
        "company_info": company_info,
        "questions": formatted_questions,

        "matching_strategy": None,
        "answers": [],
        "final_result": None,
        "quality_report": None,
        "status": "pending",
        "error": None
    }

    graph = create_generation_graph()

    try:
        final_state = await graph.ainvoke(initial_state)

        return {
            "final_result": final_state.get("final_result"),
            "quality_report": final_state.get("quality_report"),
            "status": "completed"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "final_result": None,
            "quality_report": None,
            "status": "failed",
            "error": str(e)
        }