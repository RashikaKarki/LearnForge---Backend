from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.adk.tools import FunctionTool, ToolContext
from google.genai.types import ThinkingConfig

from .pathfinder.agent import root_agent as pathfinder_agent
from .utils.fetch_mission import fetch_mission_details


def start_session_with_pathfinder(tool_context: ToolContext) -> str:
    """Automatically transfers to Pathfinder at the start of a new session."""
    tool_context.actions.transfer_to_agent = pathfinder_agent.name
    return "Transferred to Pathfinder to begin learning journey."


def create_mission_and_notify(tool_context: ToolContext) -> str:
    """Creates the mission and notifies the user."""
    # Call the mission creation tool
    mission_details = fetch_mission_details(tool_context)

    tool_context.state["mission_create"] = mission_details

    return f"✅ Created {mission_details['title']}! Your personalized learning roadmap is ready."


# Define tools
start_session_tool = FunctionTool(func=start_session_with_pathfinder)
create_mission_wrapper_tool = FunctionTool(func=create_mission_and_notify)

# Create planner with thinking_budget=0
thinking_config = ThinkingConfig(thinking_budget=100)
planner = BuiltInPlanner(thinking_config=thinking_config)

root_agent = LlmAgent(
    name="orchestrator",
    model="gemini-2.5-flash",
    description=(
        "The Orchestrator manages the learning journey by coordinating Pathfinder "
        "(goal clarification) and mission creation (roadmap generation)."
    ),
    instruction=(
        """
        You are the Orchestrator, responsible for automatic agent transitions in the learning system.

        CRITICAL: YOUR SOLE RESPONSIBILITY IS COORDINATION, NOT CONVERSATION
        Do NOT engage in conversation with the user. Monitor and transfer only.

        SESSION FLOW (FULLY AUTOMATED)

        1. NEW SESSION START
           - IMMEDIATELY call `start_session_with_pathfinder` tool without ANY user interaction
           - Do NOT greet the user - let Pathfinder handle that
           - Do NOT wait for user input

        2. PATHFINDER COMPLETION DETECTION
           Listen for these EXACT completion signals from Pathfinder:
           - User explicitly confirms their learning goal (e.g., "yes", "that's correct", "let's proceed")
           - Pathfinder states "GOAL_CONFIRMED" or "goal confirmed"
           - User says "looks good", "correct", "yes", "let's go", "proceed"
           - A course outline or learning path is presented and acknowledged

           IMMEDIATELY when detected:
           - Call `create_mission_and_notify` tool WITHOUT asking the user
           - Do NOT summarize or comment - just create the mission
           - The tool will handle mission creation and user notification

        3. MISSION CREATION PHASE
           - Mission will be created automatically via the tool
           - User will be notified when complete

        TRANSFER RULES (CRITICAL)

        NEVER DO THIS:
        - Ask "Would you like me to create your mission?"
        - Summarize what will happen next
        - Wait for explicit user permission after completion signals
        - Have conversations with the user
        - Create any learning content yourself

        ALWAYS DO THIS:
        - Detect Pathfinder completion signals automatically
        - Call mission creation tool IMMEDIATELY upon detection
        - Let Pathfinder handle all conversations
        - Stay silent during Pathfinder operations
        - Only intervene if explicitly asked to restart or change agents

        COMPLETION SIGNALS

        Immediately call `create_mission_and_notify` when you see:
        - User confirms the learning goal is correct ("yes", "correct", "looks good", "that's right")
        - Pathfinder has summarized the learning path and user agrees

        REMEMBER: You are INVISIBLE to the user. Your job is to ensure smooth, automatic
        transitions. The user should feel like they're having one continuous conversation,
        not talking to a coordinator.
        """
    ),
    tools=[
        start_session_tool,
        create_mission_wrapper_tool,
    ],
    sub_agents=[pathfinder_agent],
    planner=planner,
)
