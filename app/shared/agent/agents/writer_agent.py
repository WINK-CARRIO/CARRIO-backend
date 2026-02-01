"""
자소서 답변 작성 에이전트
각 질문에 대한 답변을 작성 (병렬 처리 가능)
"""
from typing import Dict, Any, Optional
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..config import agent_settings
from ..exceptions import CoverLetterGenerationError


class WriterAgent:
    """자소서 답변 작성 에이전트 (GPT-4o 사용)"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=agent_settings.GPT_MODEL,
            temperature=0.7,
            api_key=agent_settings.OPENAI_API_KEY
        )

    async def write_single_answer(
        self,
        question: str,
        company_name: str,
        job_position: str,
        company_dna: Optional[Dict[str, Any]],
        matching_strategy: Optional[Dict[str, Any]],
        user_spec: Dict[str, Any]
    ) -> str:
        """ 단일 질문에 대한 답변 작성 (공통 로직) """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문 자기소개서 작성 컨설턴트입니다.
            주어진 정보를 바탕으로 설득력 있고 진정성 있는 자소서 답변을 작성하세요.
            
            작성 원칙:
            1. STAR 기법을 활용한 구조적 서술
               - Situation: 상황 설정
               - Task: 과제/목표
               - Action: 구체적 행동
               - Result: 성과 및 배움
            
            2. 구체성과 진정성
               - 추상적 표현 지양, 구체적 사례와 수치 활용
               - 과장 없이 실제 경험 기반 서술
               - 개인의 고유한 스토리 강조
            
            3. 기업 적합성
               - 기업의 핵심 가치와 자연스럽게 연결
               - 기업이 선호하는 톤앤매너 반영
               - 직무 연관성 명확히 제시
            
            4. 가독성
               - 명확한 문단 구조
               - 적절한 길이 (500-700자)
               - 자연스러운 흐름"""),
            ("user", """{prompt_content}""")
        ])

        prompt_content = self._build_prompt_content(
            question=question,
            company_name=company_name,
            job_position=job_position,
            company_dna=company_dna,
            matching_strategy=matching_strategy,
            user_spec=user_spec
        )

        messages = prompt.format_messages(prompt_content=prompt_content)

        try:
            response = await self.llm.ainvoke(messages)
            answer = response.content.strip()

            char_count = len(answer)
            if char_count < 300:
                print(f"경고: 답변이 너무 짧습니다 ({char_count}자)")
            elif char_count > 900:
                print(f"경고: 답변이 너무 깁니다 ({char_count}자)")

            return answer

        except Exception as e:
            raise CoverLetterGenerationError(f"답변 작성 실패: {str(e)}")


    def _build_prompt_content(
        self,
        question: str,
        company_name: str,
        job_position: str,
        company_dna: Optional[Dict[str, Any]],
        matching_strategy: Optional[Dict[str, Any]],
        user_spec: Dict[str, Any]
    ) -> str:
        """프롬프트 컨텐츠 구성"""
        sections = []

        sections.append("## 기업 정보")
        sections.append(f"- 기업: {company_name}")
        sections.append(f"- 직무: {job_position}")

        if company_dna:
            sections.append("\n## 기업이 원하는 인재상")
            core_values = company_dna.get('core_values', [])
            ideal_traits = company_dna.get('ideal_traits', [])
            comm_tone = company_dna.get('communication_tone', '')

            sections.append(f"- 핵심가치: {', '.join(core_values)}")
            sections.append(f"- 인재특성: {', '.join(ideal_traits)}")
            sections.append(f"- 커뮤니케이션 톤: {comm_tone}")

        if matching_strategy:
            sections.append("\n## 작성 전략")
            key_points = matching_strategy.get('key_points', [])
            tone_guide = matching_strategy.get('tone_guide', '')
            differentiators = matching_strategy.get('differentiators', [])

            sections.append(f"- 핵심 포인트: {', '.join(key_points)}")
            sections.append(f"- 톤 가이드: {tone_guide}")
            sections.append(f"- 차별화 요소: {', '.join(differentiators)}")

        sections.append("\n## 지원자 정보")
        sections.append(json.dumps(user_spec, ensure_ascii=False, indent=2))

        sections.append("\n## 질문")
        sections.append(question)

        sections.append("\n## 작성 요구사항")
        sections.append("1. 500-700자 내외로 작성")
        sections.append("2. 구체적인 경험과 수치화된 성과 포함")
        sections.append("3. 기업 가치와 자연스럽게 연결")
        sections.append("4. STAR 기법 활용 (Situation, Task, Action, Result)")
        sections.append("5. 진솔하면서도 전문적인 톤 유지")
        sections.append("6. 질문의 의도에 정확히 부합하는 답변")
        sections.append("\n자소서 답변만 작성하세요 (제목이나 부가 설명 없이 본문만).")

        return "\n".join(sections)