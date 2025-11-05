from google.adk.tools import FunctionTool, ToolContext


def update_checkpoint_goal(checkpoint_goal: str, tool_context: ToolContext) -> str:
    """
    Tool to update the checkpoint goal in the mission state.
    """
    from app.agents.mission_ally.agent import root_agent as orchestrator_agent

    tool_context.state["current_checkpoint_goal"] = checkpoint_goal
    tool_context.actions.transfer_to_agent = orchestrator_agent.name
    return "Checkpoint goal updated"


update_checkpoint_goal_tool = FunctionTool(func=update_checkpoint_goal)
