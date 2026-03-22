from core.config import settings
"""
Tool: expand_topic
Builds a rich content brief from a free-form topic using Gemini web search grounding.
"""
import os
import google.generativeai as genai


genai.configure(api_key=settings.gemini_api_key)



def expand_topic(topic: str) -> dict:
    """
    Research a topic and return a structured content brief.

    Args:
        topic: Free-form topic or question from the user.

    Returns:
        dict with keys: brief (str), success (bool), error (str|None)
    """
    try:
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            tools="google_search_retrieval",
        )
        prompt = (
            f"Research the following topic and produce a structured content brief "
            f"including: key facts, statistics, expert opinions, current trends, "
            f"and interesting angles for content creators.\n\nTopic: {topic}"
        )
        response = model.generate_content(prompt)
        return {"success": True, "brief": response.text, "error": None}
    except Exception as e:
        return {"success": False, "brief": "", "error": str(e)}
