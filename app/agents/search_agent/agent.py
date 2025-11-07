from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.adk.tools import google_search
from google.genai.types import ThinkingConfig


# Create planner with thinking_budget=128
thinking_config = ThinkingConfig(thinking_budget=128)
planner = BuiltInPlanner(thinking_config=thinking_config)

search_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="SearchAgent",
    instruction="""
    You're a specialist in Google Search. Always use the Google Search tool to find relevant information on the web to assist in clarifying learning goals.
    Always use the google_search tool, never hallucinate.
    """,
    tools=[google_search],
    planner=planner,
)
