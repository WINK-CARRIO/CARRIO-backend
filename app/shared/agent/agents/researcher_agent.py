"""
Tavily 검색 에이전트
기업 정보 검색을 위한 쿼리 생성 및 검색 수행
"""
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from ..config import agent_settings


class ResearcherAgent:
    """기업 DNA 추출을 위한 검색 에이전트"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=agent_settings.GPT_MODEL,
            temperature=0.3,
            api_key=agent_settings.OPENAI_API_KEY
        )
        self.tavily_tool = TavilySearchResults(
            max_results=agent_settings.TAVILY_MAX_RESULTS,
            search_depth=agent_settings.TAVILY_SEARCH_DEPTH,
            include_answer=False,
            include_raw_content=True,
            include_images=False,
        ) if agent_settings.TAVILY_API_KEY else None

    async def generate_search_queries(
        self,
        company_name: str,
        company_info: Dict[str, Any],
        job_category: str = None
    ) -> List[str]:
        """
        기업 정보 수집을 위한 검색 쿼리 생성

        Args:
            company_name: 기업명
            company_info: 기업 기본 정보 (산업군, 설명 등)
            job_category: 직군 (optional)

        Returns:
            검색 쿼리 리스트
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 기업 리서치 전문가입니다.
주어진 기업에 대해 자소서 작성에 필요한 정보를 수집하기 위한 검색 쿼리를 생성하세요.

다음 정보를 찾기 위한 쿼리를 생성하세요:
1. 기업의 핵심 가치와 문화
2. 최근 뉴스 및 사업 방향
3. 인재상 및 채용 정보
{job_category_instruction}

각 쿼리는 구체적이고 검색 엔진에 최적화되어야 합니다.
쿼리는 3-5개 정도 생성하세요."""),
            ("user", """기업명: {company_name}
산업군: {industry}
설명: {description}
{job_category_info}

위 기업에 대한 검색 쿼리를 JSON 배열 형식으로 반환하세요.
예시: ["쿼리1", "쿼리2", "쿼리3"]""")
        ])

        job_category_instruction = ""
        job_category_info = ""
        if job_category:
            job_category_instruction = f"4. {job_category} 직군 관련 정보"
            job_category_info = f"지원 직군: {job_category}"

        messages = prompt.format_messages(
            company_name=company_name,
            industry=company_info.get("industry", "N/A"),
            description=company_info.get("description", "N/A"),
            job_category_instruction=job_category_instruction,
            job_category_info=job_category_info
        )

        response = await self.llm.ainvoke(messages)

        # JSON 파싱
        import json
        try:
            queries = json.loads(response.content)
            return queries
        except json.JSONDecodeError:
            # 파싱 실패 시 기본 쿼리 반환
            return [
                f"{company_name} 기업 문화 핵심 가치",
                f"{company_name} 최근 뉴스 사업 방향",
                f"{company_name} 인재상 채용 정보"
            ]

    async def search_with_tavily(
        self,
        queries: List[str],
        max_results_per_query: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Tavily를 사용하여 검색 수행

        Args:
            queries: 검색 쿼리 리스트
            max_results_per_query: 쿼리당 최대 결과 수

        Returns:
            검색 결과 리스트 [
                {
                    "query": "검색 쿼리",
                    "url": "결과 URL",
                    "title": "제목",
                    "content": "내용 요약"
                },
                ...
            ]
        """
        all_results = []

        if not self.tavily_tool:
            print("Tavily API 키가 설정되지 않았습니다.")
            return all_results

        for query in queries:
            try:
                # TavilySearchResults.ainvoke()는 딕셔너리를 입력으로 받음
                results = await self.tavily_tool.ainvoke({"query": query})

                # results는 리스트 형태로 반환됨
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
                # 검색 실패 시 로깅하고 계속 진행
                print(f"Tavily 검색 실패 (query: {query}): {str(e)}")
                continue

        return all_results