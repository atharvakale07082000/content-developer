from core.config import settings
"""Email newsletter drafter."""
import os
from google import genai

client = genai.Client(api_key=settings.gemini_api_key)

PROMPT = """\
You are an expert email newsletter writer. Draft a newsletter edition based on the content brief below.

Structure:
1. Subject line (compelling, under 50 chars)
2. Preview text (under 90 chars)
3. Opening (2-3 sentences — personal, warm, direct)
4. Main body (3-4 sections with subheadings, key insights, and actionable takeaways)
5. Closing CTA (one clear action)
6. Sign-off

Rules:
- Tone: {tone_angle}
- Audience: {target_audience}
- Length: 400-600 words
- No jargon. Write like a smart friend, not a marketer.

Return the full newsletter with clear section labels.
"""


def draft_newsletter(content: str, suggestion: dict) -> str:
    system = PROMPT.format(
        tone_angle=suggestion.get("tone_angle", "conversational"),
        target_audience=suggestion.get("target_audience", "subscribers"),
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=f"{system}\n\nCONTENT BRIEF:\n{content}\n\nANGLE:\n{suggestion.get('hook', '')}"
    )
    return response.text.strip()
