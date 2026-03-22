from core.config import settings
"""
Analyser sub-agent.
Takes raw content (transcript / article text / topic brief) and extracts
structured signals: themes, target audiences, tone, key insights.
Returns a JSON-serialisable dict.
"""
import os
import json
import google.generativeai as genai

genai.configure(api_key=settings.gemini_api_key)

ANALYSER_PROMPT = """\
You are a senior content strategist. Analyse the provided content and return ONLY a valid JSON object with this exact structure:

{
  "main_topic": "one-line description of the core topic",
  "key_themes": ["theme1", "theme2", "theme3"],
  "target_audiences": [
    {"audience": "description", "why": "why this content suits them"}
  ],
  "tone_of_source": "educational | conversational | technical | inspirational | controversial",
  "key_insights": ["insight1", "insight2", "insight3"],
  "content_angles": ["angle1", "angle2", "angle3"],
  "estimated_content_depth": "surface | intermediate | deep"
}

Return ONLY the JSON. No explanation, no markdown fences.
"""


def analyse_content(content: str) -> dict:
    """
    Analyse raw content and extract structured signals.

    Args:
        content: Transcript, article text, or topic brief.

    Returns:
        Structured analysis dict.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        f"{ANALYSER_PROMPT}\n\nCONTENT:\n{content[:12000]}"  # cap tokens
    )
    try:
        return json.loads(response.text.strip())
    except json.JSONDecodeError:
        # Fallback: return raw text wrapped in a dict
        return {"raw_analysis": response.text, "parse_error": True}

