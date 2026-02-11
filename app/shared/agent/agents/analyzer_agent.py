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
        scraped_contents: List[Dict[str, Any]],
        job_category: str = None
    ) -> CompanyDNA:
        """수집된 정보를 분석하여 기업 DNA 추출"""

        combined_content = self._combine_collected_data(search_results, scraped_contents)

        if not combined_content.strip():
            raise CompanyDNAExtractionError("분석할 텍스트 데이터가 없습니다.")

        system_prompt = self._build_system_prompt(job_category)

        user_msg = f"기업명: {company_name}"
        if job_category:
            user_msg += f"\n분석 대상 직군: {job_category}"
        user_msg += f"\n\n수집된 데이터:\n{combined_content[:25000]}"

        try:
            result: CompanyDNAOutput = await self.analyzer.ainvoke([
                ("system", system_prompt),
                ("user", user_msg)
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

    def _build_system_prompt(self, job_category: str = None) -> str:
        # 전사 인재상 추출
        if not job_category:
            return """당신은 기업 분석 전문가입니다.
제공된 텍스트를 분석하여 **전사 공통** 인재상과 핵심 가치를 추출하세요.

**추출 방향**:
1. 기업 전체에 적용되는 비전, 미션, 핵심 가치에 집중하세요.
2. 특정 직무가 아닌, 모든 구성원에게 요구되는 인성/태도/협업 능력을 우선하세요.
3. 기업 문화와 일하는 방식(소통, 의사결정, 성장)을 반영하세요.

**제약사항**:
- 추측보다는 텍스트에 기반한 사실을 우선하세요.
- 검색 결과에 없는 정보를 지어내지 마세요."""

        # 직무별 인재상 추출
        return f"""당신은 기업 분석 전문가입니다.
제공된 텍스트를 분석하여 **{job_category} 직군**에 특화된 인재상을 추출하세요.

**추출 방향**:
1. 이 직군에서 중요시하는 **경험의 종류와 맥락**에 집중하세요.
   예: "서비스 배포 및 운영 경험", "데이터 기반 의사결정 경험"
2. 직무에서 요구하는 **역량과 태도**(문제 해결력, 협업 방식 등)를 추출하세요.
3. 전사 공통 가치가 아닌, **이 직군만의 차별화된 요건**에 집중하세요.

**중요 제약사항**:
1. 구체적인 프로그래밍 언어나 프레임워크 이름은 검색 결과에 **명시된 경우에만** 포함하세요.
2. 검색 결과에 없는 기술 스택을 추측하거나 일반화하지 마세요.
3. 대신 "어떤 종류의 경험"을 중요시하는지 맥락 중심으로 서술하세요.
   예: "최신 기술 트렌드 학습 및 적용 능력" (O), "React 필수" (X - 명시 없으면)
4. 추측보다는 텍스트에 기반한 사실을 우선하세요."""

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