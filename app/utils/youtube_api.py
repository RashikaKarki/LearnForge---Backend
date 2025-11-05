"""YouTube Data API v3 integration for fetching educational videos."""

import re
from typing import Any

import httpx

from app.core.config import settings


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""

    pass


def search_youtube_videos(
    query: str,
    max_results: int = 3,
    duration_filter: str | None = None,
    video_category_id: str = "27",
) -> list[dict[str, Any]]:
    """
    Search YouTube for educational videos using the Data API v3.

    Args:
        query: Search query string
        max_results: Maximum number of videos to return (default: 3)
        duration_filter: Filter by duration - "short" (<4min), "medium" (4-20min), "long" (>20min)
        video_category_id: YouTube video category ID (27 = Education by default)

    Returns:
        List of video dictionaries with:
        - video_id: YouTube video ID
        - title: Video title
        - channel: Channel name
        - description: Video description
        - duration_seconds: Video duration in seconds
        - published_at: Video publication date
        - thumbnail_url: Video thumbnail URL
        - view_count: View count
        - url: Full YouTube URL

    Raises:
        YouTubeAPIError: If API call fails
    """
    api_key = settings.YOUTUBE_API_KEY

    if not api_key:
        raise YouTubeAPIError("YouTube API key not found. Set YOUTUBE_API_KEY in the settings.")

    # Build search parameters
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key,
        "videoCategoryId": video_category_id,
        "order": "relevance",
    }

    if duration_filter:
        search_params["videoDuration"] = duration_filter

    try:
        # Search for videos
        search_url = "https://www.googleapis.com/youtube/v3/search"
        with httpx.Client(timeout=10.0) as client:
            search_response = client.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()

        if "items" not in search_data or not search_data["items"]:
            return []

        # Extract video IDs
        video_ids = [item["id"]["videoId"] for item in search_data["items"]]

        # Get detailed video information (duration, statistics, etc.)
        videos_params = {
            "part": "contentDetails,snippet,statistics",
            "id": ",".join(video_ids),
            "key": api_key,
        }

        videos_url = "https://www.googleapis.com/youtube/v3/videos"
        with httpx.Client(timeout=10.0) as client:
            videos_response = client.get(videos_url, params=videos_params)
            videos_response.raise_for_status()
            videos_data = videos_response.json()

        if "items" not in videos_data:
            return []

        # Parse and format video information
        videos = []
        for video_item in videos_data["items"]:
            snippet = video_item.get("snippet", {})
            content_details = video_item.get("contentDetails", {})
            statistics = video_item.get("statistics", {})

            # Parse duration (ISO 8601 format like "PT5M30S")
            duration_str = content_details.get("duration", "PT0S")
            duration_seconds = _parse_iso8601_duration(duration_str)

            video_info = {
                "video_id": video_item["id"],
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "description": snippet.get("description", ""),
                "duration_seconds": duration_seconds,
                "duration_formatted": _format_duration(duration_seconds),
                "published_at": snippet.get("publishedAt", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "url": f"https://www.youtube.com/watch?v={video_item['id']}",
            }
            videos.append(video_info)

        return videos

    except httpx.HTTPStatusError as e:
        error_msg = f"YouTube API HTTP error: {e.response.status_code}"
        if e.response.status_code == 403:
            error_msg += " - Check API key and quotas"
        raise YouTubeAPIError(error_msg) from e
    except Exception as e:
        raise YouTubeAPIError(f"YouTube API error: {str(e)}") from e


def _parse_iso8601_duration(duration: str) -> int:
    """
    Parse ISO 8601 duration string (e.g., 'PT5M30S') to seconds.

    Args:
        duration: ISO 8601 duration string

    Returns:
        Duration in seconds
    """
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, duration)

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def _format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string like "5:30" or "1:15:00"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
