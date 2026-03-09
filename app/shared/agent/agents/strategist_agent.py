"""
전략 수립 에이전트
기업 DNA와 사용자 스펙을 매칭하여 자소서 작성 전략 수립
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from ..config import agent_settings
from ..exceptions import StrategyPlanningError
from ..state import CompanyDNA, MatchingStrategy, QuestionInfo

class QuestionStrategyModel(BaseModel):
    question_index: int = Field(description="질문 인덱스 (0부터 시작)")
    key_message: str = Field(description="이 질문에서 전달할 핵심 메시지")
    recommended_experiences: List[str] = Field(description="추천 경험 소재 (2개 내외)")
    company_value_alignment: str = Field(description="연결할 기업 핵심 가치")

class MatchingStrategyOutput(BaseModel):
    question_strategies: List[QuestionStrategyModel]

    key_points: List[str] = Field(
        default_factory=list,
        description="자소서 전체 관통 핵심 포인트 (3개)"
    )
    tone_guide: str = Field(
        default="전문적이고 자신감 있는, 논리적인 톤",
        description="전체 톤앤매너 가이드"
    )
    differentiators: List[str] = Field(
        default_factory=list,
        description="지원자만의 차별화 요소"
    )


class StrategistAgent:
    """매칭 전략 수립 에이전트 (Claude Opus/Sonnet 사용)"""

    def __init__(self):
        if not agent_settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self.llm = ChatAnthropic(
            model=agent_settings.CLAUDE_MODEL,
            temperature=0.3,
            api_key=agent_settings.ANTHROPIC_API_KEY
        )
        self.planner = self.llm.with_structured_output(MatchingStrategyOutput)

    async def create_matching_strategy(
        self,
        company_name: str,
        company_dna: Optional[CompanyDNA],
        user_spec: Dict[str, Any],
        questions: List[QuestionInfo]
    ) -> MatchingStrategy:

        # DNA 없으면 기본 전략
        if not company_dna:
            return self._create_default_strategy(questions)

        user_spec_text = self._format_user_spec(user_spec)

        questions_text = "\n".join([
            f"[{q['id']}] (Index {i}): {q['content']} (제한: {q.get('max_length', '자율')}자)"
            for i, q in enumerate(questions)
        ])

        system_prompt = """당신은 자기소개서 전략 전문가입니다.
기업 DNA와 지원자 스펙을 분석하여 최적의 매칭 전략을 수립하세요.

[필수 포함 사항]
1. 각 질문별 상세 전략 (question_strategies)
2. 전체 자소서를 관통하는 핵심 포인트 (key_points)
3. 전체적인 톤앤매너 가이드 (tone_guide) - 예: "두괄식으로 명확하게, 수치를 강조하며"
4. 지원자만의 차별화 요소 (differentiators)

위 4가지 항목을 모두 포함하여 JSON 구조로 응답해야 합니다."""

        user_msg = f"""
**기업명**: {company_name}
**기업 DNA**: {company_dna}
**지원자 스펙**: {user_spec_text}

**자소서 질문 목록**:
{questions_text}

위 정보를 바탕으로 전략을 수립해주세요.
"""

        try:
            result: MatchingStrategyOutput = await self.planner.ainvoke([
                ("system", system_prompt),
                ("user", user_msg)
            ])

            return {
                "question_strategies": [
                    {
                        "question_index": qs.question_index,
                        "question": questions[qs.question_index]['content'],
                        "recommended_experiences": qs.recommended_experiences,
                        "key_message": qs.key_message,
                        "company_value_alignment": qs.company_value_alignment
                    } for qs in result.question_strategies
                ],
                "key_points": result.key_points,
                "tone_guide": result.tone_guide,
                "differentiators": result.differentiators
            }

        except Exception as e:
            print(f"Strategist Agent Error Details: {e}")
            raise StrategyPlanningError(f"전략 수립 실패: {str(e)}")

    def _format_user_spec(self, user_spec: Dict[str, Any]) -> str:
        """사용자 스펙을 텍스트로 포맷팅"""
        sections = []
        structured = user_spec.get("structured_data", {})
        free_exps = user_spec.get("free_experiences", [])

        if edu := structured.get("education"):
            sections.append(f"학력: {edu}")
        if skills := structured.get("skills"):
            sections.append(f"기술: {', '.join(skills)}")
        if certs := structured.get("certifications"):
            cert_list = []
            for cert in certs:
                name = cert.get("name")
                date = cert.get("acquired_date")
                if date:
                    cert_list.append(f"{name}({date})")  # 취득일 있으면 포함하고 없으면 포함 안함
                else:
                    cert_list.append(f"{name}")
            sections.append(f"자격증: {', '.join(cert_list)}")
        if awards := structured.get("awards"):
            sections.append(f"수상 내역: {', '.join(awards)}")
        if langs := structured.get("language_scores"):
            lang_list = []
            for lang in langs:
                l_name = lang.get("name") or lang.get("language", "Unknown") # Dict type이 Any라서 일단 name: score로 가져옴
                l_score = lang.get("score") or lang.get("level", "")
                lang_list.append(f"{l_name}: {l_score}")
            sections.append(f"어학: {', '.join(lang_list)}")
        if exps := free_exps:
            sections.append("경험 목록:")
            for i, exp in enumerate(exps, 1):
                if isinstance(exp, dict):
                    sections.append(f"{i}. {exp.get('title')}: {exp.get('description')}")
                else:
                    sections.append(f"{i}. {exp}")
        return "\n".join(sections)

    def _create_default_strategy(self, questions: List[QuestionInfo]) -> MatchingStrategy:
        """기본 전략 생성"""
        return {
            "question_strategies": [
                {
                    "question_index": i,
                    "question": q['content'],
                    "recommended_experiences": [],
                    "key_message": "직무 강점 강조",
                    "company_value_alignment": "성장 가능성"
                } for i, q in enumerate(questions)
            ],
            "key_points": ["직무 적합성", "구체적 성과"],
            "tone_guide": "전문적이고 자신감 있는 태도",
            "differentiators": []
        }