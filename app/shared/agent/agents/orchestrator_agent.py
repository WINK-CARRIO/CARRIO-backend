"""
최종 조합 및 품질 검증 에이전트
모든 답변을 조합하고 전체적인 일관성과 품질을 검증
"""
from typing import Dict, Any, Optional, List
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from ..config import agent_settings
from ..exceptions import CoverLetterGenerationError
from ..state import CompanyDNA, MatchingStrategy, QualityReport


class OrchestratorAgent:
    """최종 조합 및 품질 검증 에이전트 (Claude Sonnet 사용)"""

    def __init__(self):
        if not agent_settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self.llm = ChatAnthropic(
            model=agent_settings.CLAUDE_MODEL,
            temperature=0.2,
            api_key=agent_settings.ANTHROPIC_API_KEY
        )

    async def orchestrate_and_verify(
        self,
        questions: List[str],
        answers: List[str],
        company_dna: Optional[CompanyDNA],
        matching_strategy: Optional[MatchingStrategy]
    ) -> Dict[str, Any]:
        """
        모든 답변을 조합하고 품질 검증

        Args:
            questions: 자소서 질문 리스트
            answers: 질문별 답변 리스트 (질문 개수와 동일)
            company_dna: 기업 DNA (CompanyDNA)
            matching_strategy: 매칭 전략 (MatchingStrategy)

        Returns:
            {
                "final_cover_letter": str,
                "quality_report": QualityReport
            }
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 자기소개서 최종 검수 전문가입니다.
            작성된 답변들을 검토하고 최종 자소서로 조합하세요.

            주요 역할:
            1. 전체 일관성 검증
               - 모든 답변 간의 논리적 흐름 확인
               - 스토리 라인의 일관성 유지
               - 중복된 내용 제거 또는 재배치

            2. 중복/모순 제거
               - 같은 경험이 반복 언급되는지 확인
               - 상충되는 내용 수정
               - 불필요한 반복 표현 제거

            3. 톤앤매너 통일
               - 전체적인 문체 통일
               - 기업 DNA에 맞는 톤 유지
               - 자연스러운 연결 추가

            4. 최종 퀄리티 체크
               - 맞춤법, 띄어쓰기 확인
               - 문장 구조 개선
               - 전문성과 진정성 균형

            반드시 JSON 형식으로만 응답하세요."""),
            ("user", """{prompt_content}""")
        ])

        prompt_content = self._build_prompt_content(
            questions=questions,
            answers=answers,
            company_dna=company_dna,
            matching_strategy=matching_strategy
        )

        messages = prompt.format_messages(prompt_content=prompt_content)

        try:
            response = await self.llm.ainvoke(messages)
            result = self._parse_json_response(response.content)

            # 유효성 검증
            self._validate_result(result)

            return result

        except json.JSONDecodeError as e:
            raise CoverLetterGenerationError(f"JSON 파싱 실패: {str(e)}")
        except Exception as e:
            raise CoverLetterGenerationError(f"최종 조합 실패: {str(e)}")

    def _build_prompt_content(
        self,
        questions: List[str],
        answers: List[str],
        company_dna: Optional[Dict[str, Any]],
        matching_strategy: Optional[Dict[str, Any]]
    ) -> str:
        """프롬프트 컨텐츠 구성"""
        sections = []

        # 기업 DNA
        if company_dna:
            sections.append("## 기업 DNA")
            sections.append(f"- 핵심가치: {', '.join(company_dna.get('core_values', []))}")
            sections.append(f"- 커뮤니케이션 톤: {company_dna.get('communication_tone', '')}")

        # 작성 전략
        if matching_strategy:
            sections.append("\n## 작성 전략")
            sections.append(f"- 톤 가이드: {matching_strategy.get('tone_guide', '')}")
            sections.append(f"- 핵심 포인트: {', '.join(matching_strategy.get('key_points', []))}")

        # 질문과 답변 (동적 개수)
        num_questions = len(questions)
        for i in range(num_questions):
            sections.append(f"\n## 질문 {i + 1}")
            sections.append(questions[i])
            sections.append(f"\n### 답변 {i + 1}")
            sections.append(answers[i] if i < len(answers) else "")

        # 작업 지시
        sections.append("\n## 작업 지시")
        sections.append(f"위 {num_questions}개의 답변을 검토하고 최종 자소서로 조합하세요.")
        sections.append("\n**반드시 아래 JSON 형식으로만 반환하세요:**")
        sections.append("""
{
  "final_cover_letter": "각 질문에 대한 최종 답변을 \\n\\n으로 구분하여 작성",
  "quality_report": {
    "overall_score": 85,
    "consistency_check": "pass 또는 improved",
    "tone_unified": "yes 또는 adjusted",
    "improvements_made": [
      "개선한 내용 1",
      "개선한 내용 2"
    ],
    "suggestions": [
      "추가 제안사항 1",
      "추가 제안사항 2"
    ]
  }
}
        """)

        sections.append("\n중요:")
        sections.append(f"- final_cover_letter는 {num_questions}개의 답변을 구분하여 작성 (\\n\\n으로 구분)")
        sections.append("- 각 답변은 해당 질문에 대한 답변임을 명확히")
        sections.append("- 중복 제거, 톤 통일, 일관성 확보")
        sections.append("- 전체적으로 자연스러운 흐름 유지")

        return "\n".join(sections)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """응답에서 JSON 추출 및 파싱"""
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        return json.loads(response)

    def _validate_result(self, result: Dict[str, Any]) -> None:
        """결과 유효성 검증"""
        if "final_cover_letter" not in result:
            raise CoverLetterGenerationError("필수 필드 누락: final_cover_letter")

        if "quality_report" not in result:
            raise CoverLetterGenerationError("필수 필드 누락: quality_report")

        quality_report = result["quality_report"]
        required_fields = ["overall_score", "consistency_check", "tone_unified"]

        for field in required_fields:
            if field not in quality_report:
                raise CoverLetterGenerationError(f"quality_report에 필수 필드 누락: {field}")
