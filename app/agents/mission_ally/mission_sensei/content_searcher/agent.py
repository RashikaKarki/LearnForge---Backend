from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.adk.tools import FunctionTool, ToolContext, agent_tool
from google.genai.types import ThinkingConfig

from app.agents.search_agent.agent import search_agent


# Create planner with thinking_budget=0
thinking_config = ThinkingConfig(thinking_budget=200)
planner = BuiltInPlanner(thinking_config=thinking_config)


def store_content_search_result(
    main_explanation: str,
    examples: list[str],
    key_points: list[str],
    sources: list[str],
    concept_name: str,
    tool_context: ToolContext,
) -> str:
    """
    Store the content search result for use by the next agent in the workflow.

    Args:
        main_explanation: 2-3 paragraphs explaining the concept clearly
        examples: List of 2-3 concrete examples
        key_points: Bullet list of 3-5 key takeaways
        sources: List of source URLs referenced
        concept_name: The concept this content explains
    """
    tool_context.state["content_search_result"] = {
        "main_explanation": main_explanation,
        "examples": examples,
        "key_points": key_points,
        "sources": sources,
        "concept_name": concept_name,
    }
    return "Content search result stored successfully. Task complete."


store_content_search_result_tool = FunctionTool(func=store_content_search_result)

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="ContentSearcher",
    instruction="""
    You are a content researcher specializing in finding high-quality educational text content.

    ## Input Data
    - Over all mission: {mission_details}
    - current checkpoint index: {current_checkpoint_index} - Index of current checkpoint (Look at byte_size_checkpoints in mission)
    - current checkpoint goal: {current_checkpoint_goal} - The specific concept
    - user_profile: {user_profile}

    ## Tools Available

    **SearchAgent (AgentTool)**
    - Purpose: Performs web searches to find educational content
    - When to call: At the START, immediately after receiving the concept
    - How many times: 1-3 times (refine query if needed)
    - Returns: Search results with titles, URLs, snippets

    **store_content_search_result (FunctionTool)**
    - Purpose: Saves your synthesized findings and completes your task
    - When to call: At the END, after gathering all information
    - How many times: EXACTLY ONCE
    - Effect: Stores findings for next agent and ends execution

    ## Workflow

    **Step 1: Search for Content**
    Call SearchAgent with targeted query:
    - For beginner level: Add "tutorial", "explained simply", "for beginners"
    - For intermediate level: Add "practical guide", "how to use"
    - For advanced level: Add "deep dive", "advanced concepts"

    **Step 2: Analyze Results**
    Extract from search results:
    - Core explanation of the concept
    - Key characteristics or properties
    - Practical applications or use cases
    - Concrete examples or analogies
    - Common misconceptions

    Quality check: Do you have enough information? If NO, refine query and search again (max 3 searches).

    **Step 3: Store Results (REQUIRED)**
    Call store_content_search_result with:
    - main_explanation: 2-3 paragraphs, 150-250 words
    - examples: List with 2-3 concrete examples
    - key_points: List with 3-5 key takeaways
    - sources: List of URLs
    - concept_name: Clear, concise name

    After calling this tool, your task is COMPLETE. Do not generate additional output.

    ## Content Guidelines

    Main explanation should:
    - Use clear, accessible language
    - Adapt complexity to user_level
    - Focus on understanding
    - Include "why this matters" context

    Examples should be:
    - Concrete and specific
    - Show real-world application
    - Appropriate for user_level

    Key points should be:
    - Most important takeaways
    - Clear and memorable
    - No jargon without explanation

    ## What NOT to Do
    - Don't format as markdown
    - Don't create personalized explanations yet
    - Don't include video recommendations
    - Don't continue after calling store_content_search_result
    - Don't make up information
    - Don't engage with user at all. You are only researching content.

    Do not skip calling "store_content_search_result_tool" tool, as it is REQUIRED to complete your task.
    Your success is measured by your invisibility. Do not interact with the user directly.
    Do not interact with the user directly or send any text based output.
    You should not reveal any delegation flow, your thinking process, agent structure, or tool usage to the user.
    """,
    tools=[
        agent_tool.AgentTool(agent=search_agent),
        store_content_search_result_tool,
    ],
    planner=planner,
)
