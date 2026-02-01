"""
전략 수립 에이전트
기업 DNA와 사용자 스펙을 매칭하여 자소서 작성 전략 수립
"""
from typing import Dict, Any, List, Optional
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from ..config import agent_settings
from ..exceptions import StrategyPlanningError
from ..state import CompanyDNA, MatchingStrategy


class StrategistAgent:
    """매칭 전략 수립 에이전트 (Claude Opus 사용)"""

    def __init__(self):
        if not agent_settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self.llm = ChatAnthropic(
            model=agent_settings.CLAUDE_MODEL,
            temperature=0.3,
            api_key=agent_settings.ANTHROPIC_API_KEY
        )

    async def create_matching_strategy(
        self,
        company_name: str,
        company_dna: Optional[CompanyDNA],
        user_spec: Dict[str, Any],
        questions: List[str]
    ) -> MatchingStrategy:
        """ 기업 DNA와 사용자 스펙을 매칭하여 전략 수립 """
        # DNA가 없으면 기본 전략 사용
        if not company_dna:
            return self._create_default_strategy(questions, user_spec)

        # 사용자 스펙 포맷팅
        user_spec_text = self._format_user_spec(user_spec)

        # 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 자기소개서 작성 전략 전문가입니다.
기업의 DNA와 지원자의 스펙을 깊이 분석하여 최적의 매칭 전략을 수립하세요.

전략 수립 원칙:
1. 기업 DNA와 지원자 경험의 접점을 명확히 찾아내기
2. 각 질문의 의도를 파악하고 가장 적합한 경험 배치
3. 전체 자소서의 스토리 라인 일관성 유지
4. 지원자만의 차별화 요소를 부각
5. 구체적이고 실행 가능한 가이드 제공

반드시 JSON 형식으로만 응답하세요."""),
            ("user", """
**기업 정보**
기업명: {company_name}

**기업 DNA**
{company_dna}

**지원자 스펙**
{user_spec}

**자소서 질문 ({num_questions}개)**
{questions_text}

위 정보를 종합하여 자소서 작성 전략을 수립하세요.

**반드시 아래 JSON 형식으로만 반환하세요:**
{{
    "question_strategies": [
        {{
            "question": "원본 질문 텍스트",
            "recommended_experiences": ["추천경험1", "추천경험2"],
            "key_message": "이 질문에서 전달할 핵심 메시지",
            "company_value_alignment": "어떤 기업 가치와 연결되는지"
        }}
    ],
    "key_points": [
        "전체 자소서에서 반드시 강조해야 할 포인트 1",
        "전체 자소서에서 반드시 강조해야 할 포인트 2",
        "전체 자소서에서 반드시 강조해야 할 포인트 3"
    ],
    "experience_to_value_mapping": {{
        "기업핵심가치1": "해당 가치를 입증할 수 있는 지원자 경험",
        "기업핵심가치2": "해당 가치를 입증할 수 있는 지원자 경험"
    }},
    "tone_guide": "전체 자소서에서 유지해야 할 톤앤매너 가이드 (기업 DNA의 communication_tone 반영)",
    "differentiators": [
        "이 지원자만의 차별화 포인트 1 (경쟁자 대비 강점)",
        "이 지원자만의 차별화 포인트 2 (경쟁자 대비 강점)"
    ]
}}

중요:
- question_strategies 배열에는 주어진 질문 개수({num_questions}개)만큼의 전략 객체가 포함되어야 합니다.
- 각 전략 객체의 "question" 필드에는 해당 질문의 원본 텍스트를 포함하세요.

전략 수립 시 고려사항:
1. 각 질문에 가장 임팩트 있는 경험을 1-2개씩 배치
2. 같은 경험을 여러 질문에서 반복하지 않도록 분산
3. 기업 DNA의 core_values, ideal_traits와 강하게 연결
4. 지원자의 강점이 최대한 부각되도록 구성
""")
        ])

        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

        messages = prompt.format_messages(
            company_name=company_name,
            company_dna=json.dumps(company_dna, ensure_ascii=False, indent=2),
            user_spec=user_spec_text,
            questions_text=questions_text,
            num_questions=len(questions)
        )

        try:
            response = await self.llm.ainvoke(messages)

            # JSON 파싱
            strategy = self._parse_json_response(response.content)

            # 유효성 검증
            self._validate_strategy(strategy, questions)

            return strategy

        except json.JSONDecodeError as e:
            raise StrategyPlanningError(f"JSON 파싱 실패: {str(e)}")
        except Exception as e:
            raise StrategyPlanningError(f"전략 수립 실패: {str(e)}")

    def _format_user_spec(self, user_spec: Dict[str, Any]) -> str:
        """사용자 스펙을 텍스트로 포맷팅"""
        sections = []

        structured_data = user_spec.get("structured_data", {})
        free_experiences = user_spec.get("free_experiences", [])

        # 학력
        if education := structured_data.get("education"):
            sections.append(f"**학력**\n{education}\n")

        # 기술 스택
        if skills := structured_data.get("skills"):
            sections.append(f"**기술 스택**\n{', '.join(skills)}\n")

        # 자격증
        if certifications := structured_data.get("certifications"):
            sections.append(f"**자격증**\n{', '.join(certifications)}\n")

        # 수상
        if awards := structured_data.get("awards"):
            sections.append(f"**수상**\n{', '.join(awards)}\n")

        # 경험
        if free_experiences:
            sections.append("**주요 경험**")
            for i, exp in enumerate(free_experiences, 1):
                if isinstance(exp, dict):
                    title = exp.get("title", "경험")
                    description = exp.get("description", "")
                    sections.append(f"{i}. {title}\n   {description}\n")
                else:
                    sections.append(f"{i}. {exp}\n")

        return "\n".join(sections)

    def _create_default_strategy(
        self,
        questions: List[str],
        user_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """기업 DNA가 없을 때 사용할 기본 전략"""
        question_strategies = []

        for question in questions:
            question_strategies.append({
                "question": question,
                "recommended_experiences": [],
                "key_message": "자신의 강점과 경험을 구체적으로 서술",
                "company_value_alignment": "일반적인 직무 역량"
            })

        return {
            "question_strategies": question_strategies,
            "key_points": [
                "구체적인 성과와 수치 제시",
                "STAR 기법을 활용한 구조적 서술",
                "직무 연관성 강조"
            ],
            "experience_to_value_mapping": {},
            "tone_guide": "진정성 있고 구체적인 톤. 과장되지 않으면서도 자신감 있는 표현 사용.",
            "differentiators": []
        }

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

    def _validate_strategy(self, strategy: Dict[str, Any], questions: List[str]) -> None:
        """전략 유효성 검증"""
        required_fields = [
            "question_strategies",
            "key_points",
            "experience_to_value_mapping",
            "tone_guide",
            "differentiators"
        ]

        for field in required_fields:
            if field not in strategy:
                raise StrategyPlanningError(f"필수 필드 누락: {field}")

        # question_strategies 검증
        if not isinstance(strategy["question_strategies"], list):
            raise StrategyPlanningError("question_strategies는 리스트여야 합니다.")

        if len(strategy["question_strategies"]) != len(questions):
            raise StrategyPlanningError(
                f"question_strategies 개수({len(strategy['question_strategies'])})가 "
                f"질문 개수({len(questions)})와 일치하지 않습니다."
            )