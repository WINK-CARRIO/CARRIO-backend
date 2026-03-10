"""
자소서 답변 작성 에이전트
각 질문에 대한 답변을 작성 (병렬 처리 가능)
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from ..config import agent_settings
from ..exceptions import CoverLetterGenerationError
from ..state import QuestionInfo, GeneratedAnswer, MatchingStrategy

class AnswerOutput(BaseModel):
    content: str = Field(description="작성된 자소서 답변 본문")
    rationale: str = Field(description="작성 의도 및 전략 설명 (짧게)")

class WriterAgent:
    """자소서 답변 작성 에이전트 (GPT-4o)"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=agent_settings.GPT_MODEL,
            temperature=0.7,
            api_key=agent_settings.OPENAI_API_KEY
        )
        self.writer = self.llm.with_structured_output(AnswerOutput)

    async def write_single_answer(
        self,
        question_info: QuestionInfo,
        question_index: int,
        company_name: str,
        company_dna: Optional[Dict[str, Any]],
        matching_strategy: Optional[MatchingStrategy],
        user_spec: Dict[str, Any]
    ) -> GeneratedAnswer:

        target_strategy = None
        if matching_strategy:
            for s in matching_strategy.get("question_strategies", []):
                if s["question_index"] == question_index:
                    target_strategy = s
                    break

        prompt_content = self._build_prompt_content(
            question_info=question_info,
            company_name=company_name,
            company_dna=company_dna,
            matching_strategy=matching_strategy,
            target_strategy=target_strategy,
            user_spec=user_spec
        )

        system_prompt = "당신은 전문 자기소개서 작성 컨설턴트입니다. STAR 기법을 활용해 구체적이고 설득력 있는 답변을 작성하세요."

        try:
            result: AnswerOutput = await self.writer.ainvoke([
                ("system", system_prompt),
                ("user", prompt_content)
            ])

            return {
                "question_index": question_index,
                "content": result.content,
                "length": len(result.content),
                "rationale": result.rationale
            }

        except Exception as e:
            raise CoverLetterGenerationError(f"답변 작성 실패 (Q{question_index}): {str(e)}")

    def _build_prompt_content(
        self,
        question_info: QuestionInfo,
        company_name: str,
        company_dna: Optional[Dict],
        matching_strategy: Optional[Dict],
        target_strategy: Optional[Dict],
        user_spec: Dict
    ) -> str:
        """프롬프트 내용 구성"""
        sections = [f"## 기업: {company_name}"]

        if company_dna:
            dna_text = []
            if core_values := company_dna.get('core_values'):
                dna_text.append(f"- 핵심 가치: {', '.join(core_values)}")
            if ideal_traits := company_dna.get('ideal_traits'):
                dna_text.append(f"- 인재상: {', '.join(ideal_traits)}")
            if keywords := company_dna.get('keywords'):
                dna_text.append(f"- 주요 키워드: {', '.join(keywords)}")
            if tone := company_dna.get('communication_tone'):
                dna_text.append(f"- 기업 커뮤니케이션 톤: {tone}")

            sections.append(f"## 기업 DNA (반영 필수):\n" + "\n".join(dna_text))

        min_len = question_info.get('min_length') or 500
        max_len = question_info.get('max_length') or 700

        sections.append(f"## 질문: {question_info['content']}")
        sections.append(f"## 제약사항: 최소 {min_len}자 ~ 최대 {max_len}자 (중요! 반드시 준수)")

        if target_strategy:
            sections.append(f"## 전략: {target_strategy.get('key_message')}")
            sections.append(f"## 추천 소재: {', '.join(target_strategy.get('recommended_experiences', []))}")

        if matching_strategy:
            sections.append(f"## 톤앤매너: {matching_strategy.get('tone_guide')}")

        sections.append(f"## 지원자 정보:\n{str(user_spec)}")

        return "\n".join(sections)