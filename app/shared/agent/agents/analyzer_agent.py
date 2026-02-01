"""
기업 DNA 분석 에이전트
수집된 정보를 분석하여 기업의 인재상과 핵심 가치를 추출
"""
from typing import Dict, Any, List
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from ..config import agent_settings
from ..exceptions import CompanyDNAExtractionError
from ..state import CompanyDNA


class AnalyzerAgent:
    """기업 DNA 추출 에이전트 (Claude Sonnet 사용)"""

    def __init__(self):
        if not agent_settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self.llm = ChatAnthropic(
            model=agent_settings.CLAUDE_MODEL,
            temperature=0.2,
            api_key=agent_settings.ANTHROPIC_API_KEY
        )

    async def extract_company_dna(
        self,
        company_name: str,
        search_results: List[Dict[str, Any]],
        scraped_contents: List[Dict[str, Any]]
    ) -> CompanyDNA:
        """
        수집된 정보를 분석하여 기업 DNA 추출

        Args:
            company_name: 기업명
            search_results: Tavily 검색 결과
            scraped_contents: Firecrawl 스크래핑 결과

        Returns:
            기업 DNA 딕셔너리 {
                "core_values": [...],
                "ideal_traits": [...],
                "keywords": [...],
                "communication_tone": "...",
                "preferred_experiences": [...]
            }
        """
        # 수집된 정보 통합
        combined_content = self._combine_collected_data(
            search_results, scraped_contents
        )

        if not combined_content.strip():
            raise CompanyDNAExtractionError("수집된 정보가 없습니다.")

        # 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 기업 문화와 인재상 분석 전문가입니다.
제공된 정보를 깊이 있게 분석하여 기업의 핵심 DNA를 추출하세요.

분석 시 주의사항:
1. 실제 수집된 정보에서 명시적으로 언급된 내용을 우선시
2. 기업의 공식 발표, 채용 공고, 임원 인터뷰 등 신뢰도가 높은 출처 우선
3. 추측보다는 근거 있는 분석
4. 일반적인 표현보다 이 기업만의 특색 있는 표현 사용
5. 자소서 작성에 실질적으로 도움이 되는 구체적인 인사이트 제공

반드시 JSON 형식으로만 응답하세요."""),
            ("user", """다음은 "{company_name}"에 대한 수집된 정보입니다.

{combined_content}

위 정보를 분석하여 이 기업의 인재상(DNA)을 추출하세요.

**반드시 아래 JSON 형식으로만 반환하세요:**
{{
    "core_values": ["핵심가치1", "핵심가치2", "핵심가치3"],
    "ideal_traits": ["인재특성1", "인재특성2", "인재특성3", "인재특성4", "인재특성5"],
    "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5", "키워드6", "키워드7", "키워드8", "키워드9", "키워드10"],
    "communication_tone": "이 기업이 선호하는 커뮤니케이션 스타일과 자소서 작성 시 권장되는 톤앤매너",
    "preferred_experiences": ["선호경험1", "선호경험2", "선호경험3"]
}}

중요:
- 각 항목은 구체적이고 실행 가능한 내용이어야 함
- core_values: 기업이 추구하는 핵심 가치 (3개)
- ideal_traits: 선호하는 인재의 특성 (5개)
- keywords: 자소서에 포함하면 좋을 키워드 (10개)
- communication_tone: 자소서 작성 시 톤앤매너 가이드
- preferred_experiences: 이 기업이 높이 평가하는 경험 유형 (3개)
""")
        ])

        messages = prompt.format_messages(
            company_name=company_name,
            combined_content=combined_content[:20000]  # 토큰 제한 고려
        )

        try:
            response = await self.llm.ainvoke(messages)

            # JSON 파싱
            company_dna = self._parse_json_response(response.content)

            # 유효성 검증
            self._validate_company_dna(company_dna)

            return company_dna

        except json.JSONDecodeError as e:
            raise CompanyDNAExtractionError(f"JSON 파싱 실패: {str(e)}")
        except Exception as e:
            raise CompanyDNAExtractionError(f"기업 DNA 추출 실패: {str(e)}")

    def _combine_collected_data(
        self,
        search_results: List[Dict[str, Any]],
        scraped_contents: List[Dict[str, Any]]
    ) -> str:
        """수집된 정보를 하나의 텍스트로 통합"""
        sections = []

        # 검색 결과 추가
        if search_results:
            sections.append("=== 검색 결과 ===\n")
            for i, result in enumerate(search_results[:10], 1):
                sections.append(f"\n[{i}] {result.get('title', 'No title')}")
                sections.append(f"출처: {result.get('url', 'No URL')}")
                sections.append(f"내용: {result.get('content', 'No content')}\n")

        # 스크래핑 결과 추가
        if scraped_contents:
            sections.append("\n=== 상세 콘텐츠 ===\n")
            for i, content in enumerate(scraped_contents[:5], 1):
                sections.append(f"\n[상세 {i}] {content.get('url', 'No URL')}")
                text = content.get('content', '')
                # 길이 제한
                max_chars = agent_settings.SCRAPE_MAX_CHARS
                sections.append(f"내용: {text[:max_chars]}\n")

        return "\n".join(sections)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """응답에서 JSON 추출 및 파싱"""
        # JSON 코드 블록 제거
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        return json.loads(response)

    def _validate_company_dna(self, dna: Dict[str, Any]) -> None:
        """기업 DNA 유효성 검증"""
        required_fields = [
            "core_values",
            "ideal_traits",
            "keywords",
            "communication_tone",
            "preferred_experiences"
        ]

        for field in required_fields:
            if field not in dna:
                raise CompanyDNAExtractionError(f"필수 필드 누락: {field}")

        # 리스트 필드 검증
        if not isinstance(dna["core_values"], list) or len(dna["core_values"]) == 0:
            raise CompanyDNAExtractionError("core_values는 비어있지 않은 리스트여야 합니다.")

        if not isinstance(dna["ideal_traits"], list) or len(dna["ideal_traits"]) == 0:
            raise CompanyDNAExtractionError("ideal_traits는 비어있지 않은 리스트여야 합니다.")

        if not isinstance(dna["keywords"], list) or len(dna["keywords"]) == 0:
            raise CompanyDNAExtractionError("keywords는 비어있지 않은 리스트여야 합니다.")