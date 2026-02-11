"""
최종 조합 및 품질 검증 에이전트
모든 답변을 조합하고 전체적인 일관성과 품질을 검증
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from ..config import agent_settings
from ..exceptions import CoverLetterGenerationError
from ..state import CompanyDNA, MatchingStrategy, GeneratedAnswer, QuestionInfo, QualityReport, FinalItem

class FinalItemModel(BaseModel):
    question: str
    answer: str
    guide_comments: List[str] = Field(
        description="사용자가 직접 수정하거나 내용을 더할 때 필요한 조언"
    )

class QualityReportModel(BaseModel):
    overall_score: int = Field(description="100점 만점 기준 점수")
    consistency_check: str = Field(description="일관성 검증 결과 (Pass/Fail/Feedback)")
    tone_unified: str = Field(description="톤앤매너 통일 여부")
    improvements_made: List[str]
    suggestions: List[str]

class OrchestratorOutput(BaseModel):
    final_items: List[FinalItemModel] = Field(description="최종 완성된 자소서 항목 리스트")
    quality_report: QualityReportModel

class OrchestratorAgent:
    """최종 조합 및 품질 검증 에이전트"""

    def __init__(self):
        if not agent_settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self.llm = ChatAnthropic(
            model=agent_settings.CLAUDE_MODEL,
            temperature=0.2,
            api_key=agent_settings.ANTHROPIC_API_KEY,
            max_tokens=agent_settings.ANTHROPIC_MAX_TOKENS,
        )
        self.reviewer = self.llm.with_structured_output(OrchestratorOutput)

    async def orchestrate_and_verify(
        self,
        questions: List[QuestionInfo],
        answers: List[GeneratedAnswer],
        company_dna: Optional[CompanyDNA],
        matching_strategy: Optional[MatchingStrategy]
    ) -> Dict[str, Any]:

        sorted_answers = sorted(answers, key=lambda x: x['question_index'])

        combined_text_list = []
        for q, a in zip(questions, sorted_answers):
            combined_text_list.append(f"""
[질문 {q['id']}]: {q['content']}
[초안 답변]:
{a['content']}
(작성 의도: {a.get('rationale', '')})
""")
        combined_text = "\n".join(combined_text_list)

        prompt_content = f"""
## 기업 DNA
{str(company_dna)}

## 매칭 전략
{str(matching_strategy)}

## 작성된 초안
{combined_text}

## 지시사항
위 내용을 검토하여 최종 자소서를 완성하세요.

**[필수 출력 형식 준수]**:
1. 반드시 `final_items` 리스트와 `quality_report` 객체 두 가지를 모두 포함해야 합니다.
2. `final_items`는 JSON 문자열이 아닌 **실제 객체 리스트(List of Objects)**여야 합니다. 
3. 절대 Markdown Code Block(```json 등)을 사용하지 마세요.

**[가이드 코멘트(guide_comments) 작성 규칙]**:
1. 절대로 작성된 내용의 요약이나 장점을 나열하지 마세요.
2. **사용자가 직접 빈칸을 채우거나 더 구체적으로 수정해야 할 부분**을 콕 집어서 조언하세요.
3. AI가 알 수 없는 **구체적인 수치(%, 금액, 기간)**나 **당시의 구체적인 감정**, **고유한 에피소드 디테일**을 추가하라고 제안하세요.

**가이드 코멘트 예시**:
- "프로젝트의 진행 기간(예: 3개월)을 명시하면 성실함이 더 돋보입니다."
- "성과를 '상당한 개선' 대신 '매출 20% 증대'와 같이 구체적인 숫자로 바꿔보세요."
- "이 부분에서 팀원들과 겪었던 갈등 상황을 조금 더 드라마틱하게 묘사해보세요."

위 규칙을 준수하여 결과물을 생성하세요.
"""

        try:
            result: OrchestratorOutput = await self.reviewer.ainvoke([
                ("system", "당신은 자소서 최종 검수 전문가이자 글쓰기 코치입니다. 답변을 다듬고 사용자에게 실질적인 수정 가이드를 제공하세요."),
                ("user", prompt_content)
            ])

            final_result: List[FinalItem] = [
                {
                    "question": item.question,
                    "answer": item.answer,
                    "guide_comments": item.guide_comments
                } for item in result.final_items
            ]

            quality_report: QualityReport = {
                "overall_score": result.quality_report.overall_score,
                "consistency_check": result.quality_report.consistency_check,
                "tone_unified": result.quality_report.tone_unified,
                "improvements_made": result.quality_report.improvements_made,
                "suggestions": result.quality_report.suggestions
            }

            return {
                "final_result": final_result,
                "quality_report": quality_report
            }

        except Exception as e:
            print(f"Orchestrator Error Details: {e}")
            raise CoverLetterGenerationError(f"최종 조합 실패: {str(e)}")