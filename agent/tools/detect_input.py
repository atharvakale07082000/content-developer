"""
Tool: detect_input_type
Classifies user input as: youtube | url | topic
"""
import re


YOUTUBE_PATTERNS = [
    r"youtube\.com/watch\?v=",
    r"youtu\.be/",
    r"youtube\.com/shorts/",
]

URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)



def detect_input_type(input_text: str) -> dict:
    """
    Classify the input as 'youtube', 'url', or 'topic'.

    Args:
        input_text: The raw string submitted by the user.

    Returns:
        dict with keys: input_type, input_text
    """
    text = input_text.strip()

    for pattern in YOUTUBE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return {"input_type": "youtube", "input_text": text}

    if URL_PATTERN.match(text):
        return {"input_type": "url", "input_text": text}

    return {"input_type": "topic", "input_text": text}
