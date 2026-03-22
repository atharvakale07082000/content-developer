from core.config import settings
"""Instagram caption drafter."""
import os
import google.generativeai as genai

genai.configure(api_key=settings.gemini_api_key)

PROMPT = """\
You are an expert Instagram content strategist. Write a high-performing Instagram caption based on the content brief below.

Rules:
- First line: scroll-stopping hook (acts as the "above the fold" preview)
- Body: engaging, story-driven or value-packed (3-5 short paragraphs)
- Use line breaks generously for readability
- End with a question or CTA to drive comments
- Add 10-15 targeted hashtags on a new line after the caption
- Suggest one emoji usage per paragraph (natural, not excessive)
- Tone: {tone_angle}
- Audience: {target_audience}
- Length: 100-200 words (caption only, excluding hashtags)

Return ONLY the caption + hashtags, ready to copy-paste.
"""


def draft_instagram(content: str, suggestion: dict) -> str:
    model = genai.GenerativeModel("gemini-2.5-flash")
    system = PROMPT.format(
        tone_angle=suggestion.get("tone_angle", "inspiring"),
        target_audience=suggestion.get("target_audience", "general audience"),
    )
    response = model.generate_content(f"{system}\n\nCONTENT BRIEF:\n{content}\n\nHOOK IDEA:\n{suggestion.get('hook', '')}")
    return response.text.strip()
