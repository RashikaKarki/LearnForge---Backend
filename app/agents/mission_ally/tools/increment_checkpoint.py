from google.adk.tools import FunctionTool, ToolContext


def increment_checkpoint(tool_context: ToolContext) -> str:
    """
    Tool to increment the checkpoint in the mission state.
    """
    mission_details = tool_context.state.get("mission_details")
    if not mission_details:
        return "Error: Mission details not found. Initialize session first."

    checkpoints = mission_details.byte_size_checkpoints
    current_index = tool_context.state.get("current_checkpoint_index", -1)

    if current_index < len(checkpoints) - 1:
        new_index = current_index + 1
        tool_context.state["current_checkpoint_index"] = new_index
        tool_context.state["current_checkpoint_goal"] = checkpoints[new_index]
        return f"Checkpoint incremented to: {checkpoints[new_index]}"
    else:
        tool_context.state["current_checkpoint_index"] = -1
        tool_context.state["current_checkpoint_goal"] = "Ended"
        return "All checkpoints completed. Mission ended."


increment_checkpoint_tool = FunctionTool(func=increment_checkpoint)
