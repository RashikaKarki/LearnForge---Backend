from google.adk.tools import FunctionTool, ToolContext


def store_video_selection(
    video_selected: bool,
    video_title: str,
    video_url: str,
    channel_name: str,
    duration_minutes: int,
    why_recommended: str,
    tool_context: ToolContext = None,
) -> str:
    """
    Store the video selection result for use by the next agent in the workflow.

    Args:
        video_selected: Whether a video was selected
        video_title: Title of the selected video (if any)
        video_url: URL of the selected video (if any)
        channel_name: Channel name (if any)
        duration_minutes: Video duration in minutes (if any)
        why_recommended: Why this video is valuable (if any)
    """
    tool_context.state["video_selection_result"] = {
        "video_selected": video_selected,
        "video_title": video_title,
        "video_url": video_url,
        "channel_name": channel_name,
        "duration_minutes": duration_minutes,
        "why_recommended": why_recommended,
    }
    return "Video selection stored successfully. Task complete."


store_video_selection_tool = FunctionTool(func=store_video_selection)
