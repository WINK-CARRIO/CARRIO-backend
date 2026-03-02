# test_scraper_agent.py
# ScraperAgent.scrape_with_firecrawl의 content 절삭 로직 테스트
#
# 배경:
#   SCRAPE_MAX_CHARS(기본 5000)으로 스크래핑 결과를 잘라야 한다.
#   이 설정이 적용되지 않으면 긴 페이지가 그대로 Analyzer 프롬프트에 들어가
#   토큰 초과 또는 API 비용 급증으로 이어진다.

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.shared.agent.agents.scraper_agent import ScraperAgent


@pytest.fixture
def scraper():
    with patch("app.shared.agent.agents.scraper_agent.ChatOpenAI"):
        return ScraperAgent()


def make_firecrawl_response(markdown: str) -> Mock:
    """Firecrawl 성공 응답 Mock 생성"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "data": {
            "markdown": markdown,
            "metadata": {"title": "테스트 페이지"}
        }
    }
    return response


class TestScrapeContentTruncation:
    """SCRAPE_MAX_CHARS 적용 검증"""

    @pytest.mark.asyncio
    async def test_long_content_is_truncated(self, scraper):
        """SCRAPE_MAX_CHARS(5000)보다 긴 콘텐츠는 잘린다"""
        long_markdown = "기업 소개 내용 " * 1000  # 약 8000자
        mock_response = make_firecrawl_response(long_markdown)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.shared.agent.agents.scraper_agent.httpx.AsyncClient", return_value=mock_client):
            results = await scraper.scrape_with_firecrawl(["https://example.com"])

        assert len(results) == 1
        assert len(results[0]["content"]) == 5000

    @pytest.mark.asyncio
    async def test_short_content_is_kept_as_is(self, scraper):
        """SCRAPE_MAX_CHARS보다 짧은 콘텐츠는 그대로 저장된다"""
        short_markdown = "짧은 기업 소개"  # 9자
        mock_response = make_firecrawl_response(short_markdown)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.shared.agent.agents.scraper_agent.httpx.AsyncClient", return_value=mock_client):
            results = await scraper.scrape_with_firecrawl(["https://example.com"])

        assert results[0]["content"] == short_markdown

    @pytest.mark.asyncio
    async def test_exact_max_chars_not_truncated(self, scraper):
        """정확히 SCRAPE_MAX_CHARS 길이는 자르지 않는다"""
        exact_markdown = "a" * 5000
        mock_response = make_firecrawl_response(exact_markdown)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.shared.agent.agents.scraper_agent.httpx.AsyncClient", return_value=mock_client):
            results = await scraper.scrape_with_firecrawl(["https://example.com"])

        assert len(results[0]["content"]) == 5000

    @pytest.mark.asyncio
    async def test_multiple_urls_all_truncated(self, scraper):
        """여러 URL 스크래핑 시 모두 절삭된다"""
        long_markdown = "X" * 10000
        mock_response = make_firecrawl_response(long_markdown)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        urls = ["https://a.com", "https://b.com", "https://c.com"]

        with patch("app.shared.agent.agents.scraper_agent.httpx.AsyncClient", return_value=mock_client):
            results = await scraper.scrape_with_firecrawl(urls)

        assert len(results) == 3
        for r in results:
            assert len(r["content"]) == 5000

    @pytest.mark.asyncio
    async def test_failed_url_skipped(self, scraper):
        """스크래핑 실패한 URL은 결과에 포함되지 않는다"""
        fail_response = Mock()
        fail_response.status_code = 500
        fail_response.text = "Internal Server Error"

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=fail_response)

        with patch("app.shared.agent.agents.scraper_agent.httpx.AsyncClient", return_value=mock_client):
            results = await scraper.scrape_with_firecrawl(["https://fail.com"])

        assert results == []
