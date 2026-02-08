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
    guide_comments: List[str] = Field(description="답변에 대한 구체적인 피드백 및 수정 제안")

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

위 내용을 검토하여 최종 자소서를 완성하세요.
각 항목별로 '수정된 답변'과 '가이드 코멘트'를 작성해야 합니다.
전체적인 흐름, 중복 제거, 톤앤매너 통일을 수행하세요.
"""

        try:
            result: OrchestratorOutput = await self.reviewer.ainvoke([
                ("system", "당신은 자소서 최종 검수 전문가입니다. 각 답변을 다듬고 평가하세요."),
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
            raise CoverLetterGenerationError(f"최종 조합 실패: {str(e)}")