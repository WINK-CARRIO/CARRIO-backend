from .researcher_agent import ResearcherAgent
from .scraper_agent import ScraperAgent
from .analyzer_agent import AnalyzerAgent
from .strategist_agent import StrategistAgent
from .writer_agent import WriterAgent
from .orchestrator_agent import OrchestratorAgent

_instances = {}

def get_agent(agent_cls):
    # 싱글톤으로 사용하기 위해 __init__에 wrapper용 함수들 생성
    if agent_cls not in _instances:
        _instances[agent_cls] = agent_cls()
    return _instances[agent_cls]

# 편의를 위한 래퍼 함수들
def get_researcher(): return get_agent(ResearcherAgent)
def get_scraper(): return get_agent(ScraperAgent)
def get_analyzer(): return get_agent(AnalyzerAgent)
def get_strategist(): return get_agent(StrategistAgent)
def get_writer(): return get_agent(WriterAgent)
def get_orchestrator(): return get_agent(OrchestratorAgent)