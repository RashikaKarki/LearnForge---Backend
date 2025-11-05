from google.adk.tools import FunctionTool, ToolContext


def mark_complete(tool_context: ToolContext) -> str:
    """
    Mark the current checkpoint as complete in the session state.

    Args:
        context: Tool context with session state
        request: Request model (no parameters needed, but keeps consistency)

    Returns:
        Confirmation message
    """
    # Get checkpoint info - current_checkpoint_goal contains the checkpoint name
    checkpoint = tool_context.state.get("current_checkpoint_goal", "current checkpoint")
    checkpoint_index = tool_context.state.get("current_checkpoint_index", -1)

    # Mark checkpoint as completed in state
    mission_details = tool_context.state.get("mission_details")
    if mission_details and hasattr(mission_details, "byte_size_checkpoints"):
        checkpoints = mission_details.byte_size_checkpoints
        if 0 <= checkpoint_index < len(checkpoints):
            # Store completed checkpoint in state
            completed_checkpoints = tool_context.state.get("completed_checkpoints", [])
            if checkpoint not in completed_checkpoints:
                completed_checkpoints.append(checkpoint)
            tool_context.state["completed_checkpoints"] = completed_checkpoints
            return f"Checkpoint '{checkpoint}' (index {checkpoint_index}) marked as complete. Great progress!"

    return f"Checkpoint '{checkpoint}' marked as complete. Great progress!"


mark_complete_tool = FunctionTool(func=mark_complete)
