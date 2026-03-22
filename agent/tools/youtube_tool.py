"""
Tool: get_youtube_transcript
Fetches transcript from a YouTube URL using youtube-transcript-api.
"""
import re
from youtube_transcript_api import YouTubeTranscriptApi



def _extract_video_id(url: str) -> str | None:
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"shorts/([a-zA-Z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None



def get_youtube_transcript(youtube_url: str) -> dict:
    """
    Fetch the transcript of a YouTube video.

    Args:
        youtube_url: Full YouTube URL.

    Returns:
        dict with keys: transcript (str), video_id (str), success (bool), error (str|None)
    """
    video_id = _extract_video_id(youtube_url)
    if not video_id:
        return {"success": False, "error": "Could not extract video ID from URL", "transcript": "", "video_id": None}

    try:
        entries = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join(e["text"] for e in entries)
        return {"success": True, "transcript": transcript, "video_id": video_id, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e), "transcript": "", "video_id": video_id}
