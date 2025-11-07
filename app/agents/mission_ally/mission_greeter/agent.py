from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from google.adk.tools import FunctionTool, ToolContext
from google.genai.types import ThinkingConfig


# Create planner with thinking_budget=0
thinking_config = ThinkingConfig(thinking_budget=0)
planner = BuiltInPlanner(thinking_config=thinking_config)


def transfer_to_orchestrator(tool_context: ToolContext):
    """
    Transfers control back to the orchestrator agent after greeting is complete.
    This signals that the greeter's job is done.
    """
    from app.agents.mission_ally.agent import root_agent as orchestrator_agent

    tool_context.actions.transfer_to_agent = orchestrator_agent.name

    return "Transferred to Orchestrator to continue the learning journey."


transfer_to_orchestrator_tool = FunctionTool(func=transfer_to_orchestrator)

root_agent = LlmAgent(
    name="lumina_greeter",
    model="gemini-2.5-flash",
    description=(
        "Agent that welcomes users to their learning mission and sets the tone for the experience."
    ),
    instruction=(
        """
        You are the greeter agent of Lumina, responsible for welcoming users and setting the tone for their learning journey.

        Tone: Friendly, Supportive, Encouraging, Patient.

        Here is information of the user: {user_profile}

        STRICT ACTION FLOW:

        Step 1: Welcome the User
            - Greet the user warmly.
            - Express excitement about their learning journey.
            - Set a positive and encouraging tone.

        Step 2: Transfer Control (IMMEDIATELY after greeting)
            - Use the transfer_to_orchestrator_tool tool
            - DO NOT wait for user response
            - DO NOT engage in conversation
            - Your role is complete after greeting

        Important Notes:
            - Persona: Never expose internal tool or sub-agent names. Speak as "I" (Lumina).
            - The greeting should be brief and welcoming (2-4 sentences max)
            - IMMEDIATELY call transfer_to_orchestrator_tool after your greeting message
            - Do not ask questions or wait for responses
        """
    ),
    tools=[transfer_to_orchestrator_tool],
    planner=planner,
)
