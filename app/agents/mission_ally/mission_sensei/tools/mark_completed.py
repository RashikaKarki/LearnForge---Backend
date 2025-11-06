from google.adk.tools import FunctionTool, ToolContext


def mark_complete(tool_context: ToolContext) -> str:
    """
    Mark the current checkpoint as complete in the session state.

    Args:
        tool_context: Tool context with session state

    Returns:
        Confirmation message
    """
    checkpoint_index = tool_context.state.get("current_checkpoint_index", -1)

    mission_details = tool_context.state.get("mission_details")
    if mission_details:
        if isinstance(mission_details, dict):
            checkpoints = mission_details.get("byte_size_checkpoints", [])
        elif hasattr(mission_details, "byte_size_checkpoints"):
            checkpoints = mission_details.byte_size_checkpoints
        else:
            checkpoints = []

        if 0 <= checkpoint_index < len(checkpoints):
            # Mark all checkpoints up to and including current index as complete
            completed_checkpoints = checkpoints[: checkpoint_index + 1]
            tool_context.state["completed_checkpoints"] = completed_checkpoints

            checkpoint_name = checkpoints[checkpoint_index]
            return f"Checkpoint '{checkpoint_name}' (index {checkpoint_index}) marked as complete. Progress: {len(completed_checkpoints)}/{len(checkpoints)} checkpoints completed!"

    return "Mission not found. Initialize session first."


mark_complete_tool = FunctionTool(func=mark_complete)
