"""
Firecrawl 스크래핑 에이전트
검색 결과에서 URL을 추출하고 웹 스크래핑 수행
"""

from typing import List, Dict, Any
import httpx
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from ..config import agent_settings
from ..exceptions import ScrapingError

class TargetUrls(BaseModel):
    urls: List[str] = Field(description="스크래핑할 URL 리스트")

class ScraperAgent:
    """웹 스크래핑 에이전트"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=agent_settings.GPT_MODEL,
            temperature=0.1,
            api_key=agent_settings.OPENAI_API_KEY
        )
        self.url_selector = self.llm.with_structured_output(TargetUrls)

    async def extract_urls_to_scrape(
        self,
        search_results: List[Dict[str, Any]],
        max_urls: int = 5  # Default 값이므로 url 개수 바꾸고 싶을 때는 여기 말고 node.py에서 파라미터 값 변경
    ) -> List[str]:
        """검색 결과에서 스크래핑할 URL 선별"""

        if not search_results:
            return []

        results_summary = "\n".join([
            f"{i+1}. [{res.get('title')}]({res.get('url')}) - {res.get('content')[:100]}..."
            for i, res in enumerate(search_results[:15]) # 상위 15개만 분석 (변경 가능)
        ])

        system_prompt = f"""당신은 웹 리서치 전문가입니다.
검색 결과 중에서 자소서 작성(기업 분석)에 가장 유용한 URL을 최대 {max_urls}개 선별하세요.
우선순위: 공식 홈페이지(인재상, 소개), 기술 블로그, 최신 인터뷰 기사.
제약사항(중요): pdf 문서는 제외할 것."""

        try:
            result: TargetUrls = await self.url_selector.ainvoke([
                ("system", system_prompt),
                ("user", f"검색 결과:\n{results_summary}")
            ])
            return result.urls[:max_urls]
        except Exception:
            # 실패 시 상위 url 개수대로 그대로 반환
            return [r["url"] for r in search_results[:max_urls] if r.get("url")]

    async def scrape_with_firecrawl(
        self,
        urls: List[str]
    ) -> List[Dict[str, Any]]:
        """Firecrawl을 사용하여 웹 스크래핑 수행"""

        if not agent_settings.FIRECRAWL_API_KEY:
            raise ScrapingError("Firecrawl API 키가 설정되지 않았습니다.")

        scraped_results = []

        async with httpx.AsyncClient(timeout=agent_settings.SCRAPE_TIMEOUT) as client:
            for url in urls:
                try:
                    response = await client.post(
                        "[https://api.firecrawl.dev/v0/scrape](https://api.firecrawl.dev/v0/scrape)",
                        headers={
                            "Authorization": f"Bearer {agent_settings.FIRECRAWL_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "url": url,
                            "pageOptions": {"onlyMainContent": True}
                        }
                    )

                    if response.status_code != 200:
                        print(f"Firecrawl Error ({response.status_code}): {response.text}")
                        continue

                    data = response.json()
                    if data.get("success"):
                        scraped_results.append({
                            "url": url,
                            "content": data["data"].get("content", ""),
                            "metadata": data["data"].get("metadata", {})
                        })
                except Exception as e:
                    print(f"스크래핑 실패 ({url}): {e}")
                    # 개별 실패는 무시하고 진행
                    continue

        return scraped_results