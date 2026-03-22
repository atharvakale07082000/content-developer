from core.config import settings
"""
Suggester sub-agent.
Takes the analysis dict and returns a ranked list of content suggestions
with format, hook, audience, tone angle, and reasoning.
"""
import os
import json
import google.generativeai as genai

genai.configure(api_key=settings.gemini_api_key)

SUGGESTER_PROMPT = """\
You are an expert content strategist specialising in social media, newsletters, and SEO.

Given a content analysis, generate a ranked list of content suggestions.
Each suggestion must specify:
- format: one of "linkedin" | "newsletter" | "instagram"
- hook: a compelling opening line or headline (max 15 words)
- target_audience: who this is for (1-2 sentences)
- tone_angle: e.g. "educational", "story-driven", "contrarian", "behind-the-scenes"
- why_this_works: one sentence rationale
- estimated_engagement: "low" | "medium" | "high"

Return ONLY a valid JSON array of 4-6 suggestions, sorted by estimated_engagement descending.
No explanation, no markdown fences.
"""


def generate_suggestions(analysis_json: str) -> list:
    """
    Generate ranked content suggestions from a content analysis.

    Args:
        analysis_json: JSON string of the analysis dict from the analyser agent.

    Returns:
        List of suggestion dicts.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        f"{SUGGESTER_PROMPT}\n\nANALYSIS:\n{analysis_json}"
    )
    try:
        return json.loads(response.text.strip())
    except json.JSONDecodeError:
        return [{"raw": response.text, "parse_error": True}]

