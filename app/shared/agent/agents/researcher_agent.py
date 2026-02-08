"""
Tavily 검색 에이전트
기업 정보 검색을 위한 쿼리 생성 및 검색 수행
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from ..config import agent_settings
from ..exceptions import SearchError

class SearchQueries(BaseModel):
    queries: List[str] = Field(description="검색 엔진에 입력할 쿼리 리스트")

class ResearcherAgent:
    """기업 DNA 추출을 위한 검색 에이전트"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=agent_settings.GPT_MODEL,
            temperature=0.3,
            api_key=agent_settings.OPENAI_API_KEY
        )
        self.query_generator = self.llm.with_structured_output(SearchQueries)

        if not agent_settings.TAVILY_API_KEY:
            print("Warning: TAVILY_API_KEY is missing.")
            self.tavily_tool = None
        else:
            self.tavily_tool = TavilySearchResults(
                max_results=agent_settings.TAVILY_MAX_RESULTS,
                search_depth="advanced",
                include_answer=False,
                include_raw_content=True,
                include_images=False,
            )

    async def generate_search_queries(
        self,
        company_name: str,
        company_info: Dict[str, Any],
        job_category: str = None
    ) -> List[str]:
        """기업 정보 수집을 위한 검색 쿼리 생성"""

        system_prompt = """당신은 기업 리서치 전문가입니다.
주어진 기업에 대해 자소서 작성에 필요한 정보를 수집하기 위한 검색 쿼리를 생성하세요.
반드시 다음 정보를 찾기 위한 쿼리를 포함하세요:
1. 기업의 핵심 가치와 문화
2. 최근 뉴스 및 사업 방향
3. 인재상 및 채용 정보
"""
        user_msg = f"기업명: {company_name}\n산업군: {company_info.get('industry', 'N/A')}\n설명: {company_info.get('description', 'N/A')}"

        if job_category:
            user_msg += f"\n지원 직군: {job_category} (관련 기술 스택이나 직무 문화 포함)"

        try:
            result: SearchQueries = await self.query_generator.ainvoke([
                ("system", system_prompt),
                ("user", user_msg)
            ])
            return result.queries
        except Exception as e:
            print(f"쿼리 생성 실패: {e}")
            return [
                f"{company_name} 인재상 핵심가치",
                f"{company_name} 최근 뉴스",
                f"{company_name} 채용 블로그"
            ]

    async def search_with_tavily(
        self,
        queries: List[str],
        max_results_per_query: int = 3
    ) -> List[Dict[str, Any]]:
        """Tavily를 사용하여 검색 수행"""

        if not self.tavily_tool:
            raise SearchError("Tavily API 키가 설정되지 않아 검색을 수행할 수 없습니다.")

        all_results = []
        for query in queries:
            try:
                results = await self.tavily_tool.ainvoke({"query": query})

                if isinstance(results, list):
                    for result in results[:max_results_per_query]:
                        all_results.append({
                            "query": query,
                            "url": result.get("url"),
                            "title": result.get("title", ""),
                            "content": result.get("content", ""),
                            "score": result.get("score", 0)
                        })
            except Exception as e:
                # 개별 쿼리 실패는 예외 던지지 않고 로그만 남김
                print(f"Tavily 검색 부분 실패 (query: {query}): {str(e)}")
                continue

        if not all_results and queries:
            print("경고: 검색 결과가 없습니다.")

        return all_results