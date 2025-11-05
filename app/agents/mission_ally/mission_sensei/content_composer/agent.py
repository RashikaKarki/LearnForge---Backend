from google.adk.agents import SequentialAgent

from ..content_searcher.agent import root_agent as content_searcher
from ..video_selector.agent import root_agent as video_selector
from ..content_formatter.agent import root_agent as content_formatter

root_agent = SequentialAgent(
    name="ContentComposer",
    description="Composes personalized educational content through search, video selection, and formatting",
    sub_agents=[
        content_searcher,
        video_selector,
        content_formatter,
    ],
)
