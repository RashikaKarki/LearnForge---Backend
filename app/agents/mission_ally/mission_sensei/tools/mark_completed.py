import logging

from google.adk.tools import FunctionTool, ToolContext


logger = logging.getLogger(__name__)


def mark_complete(tool_context: ToolContext) -> str:
    """
    Mark the current checkpoint as complete in the session state.

    Args:
        tool_context: Tool context with session state

    Returns:
        Confirmation message
    """
    logger.info("[mark_complete_tool] Marking checkpoint as complete...")
    checkpoint_index = tool_context.state.get("current_checkpoint_index", -1)

    mission_details = tool_context.state.get("mission_details")
    if mission_details:
        if isinstance(mission_details, dict):
            checkpoints = mission_details.get("byte_size_checkpoints", [])
        elif hasattr(mission_details, "byte_size_checkpoints"):
            checkpoints = mission_details.byte_size_checkpoints
        elif isinstance(mission_details, list) and len(mission_details) > 0:
            first_mission = mission_details[0]
            if isinstance(first_mission, dict):
                checkpoints = first_mission.get("byte_size_checkpoints", [])
            elif hasattr(first_mission, "byte_size_checkpoints"):
                checkpoints = first_mission.byte_size_checkpoints
            else:
                checkpoints = []
        else:
            checkpoints = []

        if 0 <= checkpoint_index < len(checkpoints):
            # Mark all checkpoints up to and including current index as complete
            completed_checkpoints = checkpoints[: checkpoint_index + 1]
            tool_context.state["completed_checkpoints"] = completed_checkpoints

            checkpoint_name = checkpoints[checkpoint_index]
            logger.info(
                f"[mark_complete_tool] Checkpoint '{checkpoint_name}' (index {checkpoint_index}) marked as complete."
            )
            return f"Checkpoint '{checkpoint_name}' (index {checkpoint_index}) marked as complete. Progress: {len(completed_checkpoints)}/{len(checkpoints)} checkpoints completed!"

    logger.info("[mark_complete_tool] Mission completed successfully.")
    return "Mission completed successfully."


mark_complete_tool = FunctionTool(func=mark_complete)
