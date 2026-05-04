"""
Tool: expand_topic
Builds a rich content brief from a free-form topic.

Model: Qwen/Qwen2.5-72B-Instruct
Chosen as the most capable free model on HuggingFace Hub — well-suited
for knowledge-intensive research and structured briefing tasks.
Note: uses model knowledge rather than live web search (no Google Search grounding).
"""
from agent.hf_client import hf_chat

MODEL = "Qwen/Qwen2.5-72B-Instruct"

SYSTEM = (
    "You are a thorough research assistant and content strategist. "
    "Produce detailed, factually grounded content briefs using your training knowledge."
)

PROMPT = """\
Research the following topic and produce a structured content brief.

Include:
- Key facts and background context
- Notable statistics or data points (from your knowledge)
- Expert opinions and prevailing viewpoints
- Current trends and developments
- Interesting angles and hooks for content creators
- Potential controversies or debates
- Target audiences who would care about this topic

Topic: {topic}

Format your response clearly with headings for each section.
"""


def expand_topic(topic: str) -> dict:
    """
    Research a topic and return a structured content brief.

    Args:
        topic: Free-form topic or question from the user.

    Returns:
        dict with keys: brief (str), success (bool), error (str|None)
    """
    try:
        prompt = PROMPT.format(topic=topic)
        brief = hf_chat(MODEL, prompt, max_tokens=2048, temperature=0.5, system=SYSTEM)
        return {"success": True, "brief": brief, "error": None}
    except Exception as e:
        return {"success": False, "brief": "", "error": str(e)}
