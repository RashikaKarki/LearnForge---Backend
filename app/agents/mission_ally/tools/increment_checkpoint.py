import logging

from google.adk.tools import FunctionTool, ToolContext


logger = logging.getLogger(__name__)


def increment_checkpoint(tool_context: ToolContext) -> str:
    """
    Tool to increment the checkpoint in the mission state.
    """
    logger.info("[increment_checkpoint_tool] Incrementing checkpoint...")
    mission_details = tool_context.state.get("mission_details")
    if not mission_details:
        logger.error("[increment_checkpoint_tool] Mission details not found in state.")
        return "Error: Mission details not found. Initialize session first."

    # Handle both dict and object representations
    if isinstance(mission_details, dict):
        checkpoints = mission_details.get("byte_size_checkpoints", [])
    elif hasattr(mission_details, "byte_size_checkpoints"):
        checkpoints = mission_details.byte_size_checkpoints
    elif isinstance(mission_details, (list | tuple)) and len(mission_details) > 0:
        first_item = mission_details[0]
        if isinstance(first_item, dict):
            checkpoints = first_item.get("byte_size_checkpoints", [])
        elif hasattr(first_item, "byte_size_checkpoints"):
            checkpoints = first_item.byte_size_checkpoints
        else:
            logger.error("[increment_checkpoint_tool] Mission details format is unrecognized.")
            return "Error: Mission details format is unrecognized."
    else:
        logger.error("[increment_checkpoint_tool] Mission details missing byte_size_checkpoints.")
        return "Error: Mission details missing byte_size_checkpoints."

    current_index = tool_context.state.get("current_checkpoint_index", -1)

    if current_index < len(checkpoints) - 1:
        new_index = current_index + 1
        tool_context.state["current_checkpoint_index"] = new_index
        tool_context.state["current_checkpoint_goal"] = checkpoints[new_index]
        logger.info(
            f"[increment_checkpoint_tool] Checkpoint incremented to index {new_index}: {checkpoints[new_index]}"
        )
        return f"Checkpoint incremented to: {checkpoints[new_index]}"
    else:
        tool_context.state["current_checkpoint_index"] = -1
        tool_context.state["current_checkpoint_goal"] = "Ended"
        logger.info("[increment_checkpoint_tool] All checkpoints completed. Mission ended.")
        return "All checkpoints completed. Mission ended."


increment_checkpoint_tool = FunctionTool(func=increment_checkpoint)
