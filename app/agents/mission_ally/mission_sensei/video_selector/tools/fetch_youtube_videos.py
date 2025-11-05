from google.adk.tools import FunctionTool, ToolContext
from pydantic import BaseModel, Field

from app.utils.youtube_api import YouTubeAPIError, search_youtube_videos


class YouTubeVideoSearchResponse(BaseModel):
    """Response model for YouTube video search tool."""

    videos: list[dict] = Field(..., description="List of video information")
    count: int = Field(..., description="Number of videos found")
    note: str = Field(default="", description="Additional notes")


def fetch_youtube_videos(
    search_query: str, tool_context: ToolContext
) -> YouTubeVideoSearchResponse:
    """
    Search YouTube for educational videos using the YouTube Data API v3.

    This tool allows the LLM to generate intelligent search queries and analyze
    video metadata (titles, descriptions, durations) to find the best matches.
    """
    try:
        duration_filter = "medium"

        videos = search_youtube_videos(
            query=search_query,
            max_results=3,
            duration_filter=duration_filter,
        )

        if not videos:
            return YouTubeVideoSearchResponse(
                videos=[],
                count=0,
                note="No videos found for the given query.",
            )

        # Format response for LLM analysis
        video_info = []
        for video in videos:
            video_info.append(
                {
                    "video_id": video["video_id"],
                    "title": video["title"],
                    "channel": video["channel"],
                    "description": (
                        video["description"][:500] + "..."
                        if len(video["description"]) > 500
                        else video["description"]
                    ),
                    "duration_seconds": video["duration_seconds"],
                    "duration_formatted": video["duration_formatted"],
                    "url": video["url"],
                    "view_count": video["view_count"],
                }
            )

        return YouTubeVideoSearchResponse(
            videos=video_info,
            count=len(video_info),
            note="Analyze these videos' titles, descriptions, and durations to select the best one (or none if unsuitable).",
        )

    except YouTubeAPIError as e:
        return YouTubeVideoSearchResponse(
            videos=[],
            count=0,
            note=f"YouTube API error: {str(e)}",
        )
    except Exception as e:
        return YouTubeVideoSearchResponse(
            videos=[],
            count=0,
            note=f"Error fetching videos: {str(e)}",
        )


fetch_youtube_videos_tool = FunctionTool(func=fetch_youtube_videos)
