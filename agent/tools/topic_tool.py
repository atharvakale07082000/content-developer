from core.config import settings
"""
Tool: expand_topic
Builds a rich content brief from a free-form topic using Gemini web search grounding.
"""
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=settings.gemini_api_key)



def expand_topic(topic: str) -> dict:
    """
    Research a topic and return a structured content brief.

    Args:
        topic: Free-form topic or question from the user.

    Returns:
        dict with keys: brief (str), success (bool), error (str|None)
    """
    try:
        prompt = (
            f"Research the following topic and produce a structured content brief "
            f"including: key facts, statistics, expert opinions, current trends, "
            f"and interesting angles for content creators.\n\nTopic: {topic}"
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return {"success": True, "brief": response.text, "error": None}
    except Exception as e:
        return {"success": False, "brief": "", "error": str(e)}
