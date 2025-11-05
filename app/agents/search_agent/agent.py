from google.adk.agents import LlmAgent
from google.adk.tools import google_search

search_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="SearchAgent",
    instruction="""
    You're a specialist in Google Search
    """,
    tools=[google_search],
)
