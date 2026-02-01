"""
Firecrawl 스크래핑 에이전트
검색 결과에서 URL을 추출하고 웹 스크래핑 수행
"""
from typing import List, Dict, Any
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..config import agent_settings


class ScraperAgent:
    """웹 스크래핑 에이전트"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=agent_settings.GPT_MODEL,
            temperature=0.1,
            api_key=agent_settings.OPENAI_API_KEY
        )

    async def extract_urls_to_scrape(
        self,
        search_results: List[Dict[str, Any]],
        max_urls: int = 5
    ) -> List[str]:
        """
        검색 결과에서 스크래핑할 URL 선별

        Args:
            search_results: Tavily 검색 결과
            max_urls: 최대 URL 개수

        Returns:
            스크래핑할 URL 리스트
        """
        if not search_results:
            return []

        # 검색 결과 요약 생성
        results_summary = []
        for i, result in enumerate(search_results[:20], 1):  # 최대 20개까지만 고려
            results_summary.append(
                f"{i}. [{result.get('title', 'No title')}]({result.get('url')})\n"
                f"   검색어: {result.get('query', 'N/A')}\n"
                f"   요약: {result.get('content', 'N/A')[:100]}..."
            )

        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 웹 리서치 전문가입니다.
검색 결과 중에서 자소서 작성에 가장 유용한 정보를 담고 있는 URL을 선별하세요.

선별 기준:
1. 기업의 공식 웹사이트 우선 (채용 페이지, 회사 소개 등)
2. 신뢰할 수 있는 뉴스 기사
3. 최신 정보
4. 기업 문화, 가치, 인재상 관련 내용

최대 {max_urls}개의 URL을 선택하고, URL만 JSON 배열로 반환하세요.
예시: ["url1", "url2", "url3"]"""),
            ("user", """검색 결과:
{results_summary}

위 결과에서 스크래핑할 URL을 선별하여 JSON 배열로 반환하세요.""")
        ])

        messages = prompt.format_messages(
            max_urls=max_urls,
            results_summary="\n\n".join(results_summary)
        )

        response = await self.llm.ainvoke(messages)

        # JSON 파싱
        import json
        try:
            urls = json.loads(response.content)
            return urls[:max_urls]
        except json.JSONDecodeError:
            # 파싱 실패 시 상위 결과의 URL 반환
            return [r["url"] for r in search_results[:max_urls] if r.get("url")]

    async def scrape_with_firecrawl(
        self,
        urls: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Firecrawl을 사용하여 웹 스크래핑 수행

        Args:
            urls: 스크래핑할 URL 리스트

        Returns:
            스크래핑 결과 리스트 [
                {
                    "url": "URL",
                    "content": "스크래핑된 내용",
                    "metadata": {...}
                },
                ...
            ]
        """
        if not agent_settings.FIRECRAWL_API_KEY:
            # API 키가 없으면 스크래핑 스킵
            return [{
                "url": url,
                "content": f"[Firecrawl API 키 없음] URL: {url}",
                "metadata": {"status": "no_api_key"}
            } for url in urls]

        scraped_results = []

        async with httpx.AsyncClient(timeout=agent_settings.SCRAPE_TIMEOUT) as client:
            for url in urls:
                try:
                    # Firecrawl API 호출
                    response = await client.post(
                        "https://api.firecrawl.dev/v0/scrape",
                        headers={
                            "Authorization": f"Bearer {agent_settings.FIRECRAWL_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={"url": url}
                    )
                    response.raise_for_status()
                    data = response.json()

                    scraped_results.append({
                        "url": url,
                        "content": data.get("data", {}).get("content", ""),
                        "metadata": data.get("data", {}).get("metadata", {})
                    })
                except Exception as e:
                    # 스크래핑 실패 시 로깅하고 계속 진행
                    print(f"Firecrawl 스크래핑 실패 (url: {url}): {str(e)}")
                    scraped_results.append({
                        "url": url,
                        "content": "",
                        "metadata": {"error": str(e)}
                    })

        return scraped_results