from core.config import settings
"""LinkedIn post drafter."""
import os
from google import genai

client = genai.Client(api_key=settings.gemini_api_key)

PROMPT = """\
You are an expert LinkedIn ghostwriter. Write a high-performing LinkedIn post based on the content brief and suggestion below.

Rules:
- Start with a bold hook (first line must stop the scroll)
- Use short paragraphs (1-3 lines max)
- Include a personal or relatable angle
- End with a clear call-to-action or thought-provoking question
- Add 3-5 relevant hashtags at the end
- Length: 150-300 words
- Tone: {tone_angle}
- Target audience: {target_audience}

Return ONLY the post text, ready to copy-paste.
"""


def draft_linkedin(content: str, suggestion: dict) -> str:
    system = PROMPT.format(
        tone_angle=suggestion.get("tone_angle", "professional"),
        target_audience=suggestion.get("target_audience", "professionals"),
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=f"{system}\n\nCONTENT BRIEF:\n{content}\n\nSUGGESTED HOOK:\n{suggestion.get('hook', '')}"
    )
    return response.text.strip()
