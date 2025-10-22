from google.adk.agents import SequentialAgent

from ..mission_content_weaver.agent import \
    root_agent as mission_content_weaver_agent
from ..mission_curator.agent import root_agent as mission_curator_agent

root_agent = SequentialAgent(
    name="mission_director",
    description=(
        "Sequential coordinator that automatically executes Mission Curator followed by "
        "Mission Content Weaver. Once triggered, it runs both agents in sequence without "
        "requiring additional orchestration."
    ),
    sub_agents=[
        mission_curator_agent,
        mission_content_weaver_agent,
    ],
)
