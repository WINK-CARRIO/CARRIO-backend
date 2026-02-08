"""
기업 DNA 분석 에이전트
수집된 정보를 분석하여 기업의 인재상과 핵심 가치를 추출
"""
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from ..config import agent_settings
from ..exceptions import CompanyDNAExtractionError
from ..state import CompanyDNA  # TypedDict Import

class CompanyDNAOutput(BaseModel):
    core_values: List[str] = Field(description="기업 핵심 가치 (3개 내외)")
    ideal_traits: List[str] = Field(description="선호하는 인재 특성 (5개 내외)")
    keywords: List[str] = Field(description="자소서용 추천 키워드 (10개 내외)")
    communication_tone: str = Field(description="자소서 작성 톤앤매너 가이드")
    preferred_experiences: List[str] = Field(description="기업이 선호하는 경험 유형")

class AnalyzerAgent:
    """기업 DNA 추출 에이전트"""

    def __init__(self):
        if not agent_settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self.llm = ChatAnthropic(
            model=agent_settings.CLAUDE_MODEL,
            temperature=0.2,
            api_key=agent_settings.ANTHROPIC_API_KEY
        )
        self.analyzer = self.llm.with_structured_output(CompanyDNAOutput)

    async def extract_company_dna(
        self,
        company_name: str,
        search_results: List[Dict[str, Any]],
        scraped_contents: List[Dict[str, Any]]
    ) -> CompanyDNA:
        """수집된 정보를 분석하여 기업 DNA 추출"""

        combined_content = self._combine_collected_data(search_results, scraped_contents)

        if not combined_content.strip():
            raise CompanyDNAExtractionError("분석할 텍스트 데이터가 없습니다.")

        system_prompt = """당신은 기업 분석 전문가입니다.
제공된 텍스트를 분석하여 자소서 작성에 필요한 '기업 DNA'를 추출하세요.
추측보다는 텍스트에 기반한 사실을 우선하세요."""

        try:
            result: CompanyDNAOutput = await self.analyzer.ainvoke([
                ("system", system_prompt),
                ("user", f"기업명: {company_name}\n\n데이터:\n{combined_content[:25000]}") # 토큰 제한 고려
            ])

            return {
                "core_values": result.core_values,
                "ideal_traits": result.ideal_traits,
                "keywords": result.keywords,
                "communication_tone": result.communication_tone,
                "preferred_experiences": result.preferred_experiences
            }

        except Exception as e:
            raise CompanyDNAExtractionError(f"DNA 분석 중 오류 발생: {str(e)}")

    def _combine_collected_data(
        self,
        search_results: List[Dict[str, Any]],
        scraped_contents: List[Dict[str, Any]]
    ) -> str:
        """수집된 정보를 하나의 텍스트로 통합"""
        lines = ["=== 검색 요약 ==="]
        for res in search_results:
            lines.append(f"- {res.get('title')}: {res.get('content')}")

        lines.append("\n=== 상세 스크랩 ===")
        for content in scraped_contents:
            text = content.get('content', '')
            # 너무 긴 텍스트는 잘라서 넣기
            lines.append(f"Source: {content.get('url')}\nContent: {text[:4000]}...")

        return "\n".join(lines)