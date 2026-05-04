"""
SuggesterAgent — generates ranked content format suggestions from analysis.

Model: HuggingFaceH4/zephyr-7b-beta
Chosen for creative ideation and diverse, well-structured suggestion lists.
"""
import json
from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from agent.hf_client import hf_chat, extract_json_block


class SuggesterAgent(BaseAgent):
    agent_id = "suggester"
    capabilities = ["suggest"]
    model = "HuggingFaceH4/zephyr-7b-beta"

    _SYSTEM = (
        "You are an expert content strategist specialising in social media, newsletters, "
        "and SEO. You always respond with a valid JSON array only — no markdown, no explanation."
    )

    _PROMPT = """\
Given the content analysis below, generate a ranked list of content suggestions.
Each suggestion must contain:
- format: one of "linkedin" | "newsletter" | "instagram"
- hook: a compelling opening line or headline (max 15 words)
- target_audience: who this is for (1-2 sentences)
- tone_angle: e.g. "educational", "story-driven", "contrarian", "behind-the-scenes"
- why_this_works: one sentence rationale
- estimated_engagement: "low" | "medium" | "high"

Return ONLY a valid JSON array of 4-6 suggestions, sorted by estimated_engagement descending.
No explanation, no markdown fences.

ANALYSIS:
{analysis}
"""

    def run(self, task: AgentTask) -> AgentResult:
        try:
            analysis = task.payload["analysis"]
            prompt = self._PROMPT.format(analysis=analysis)
            raw = hf_chat(self.model, prompt, max_tokens=1500, temperature=0.75, system=self._SYSTEM)
            try:
                output = json.loads(extract_json_block(raw))
            except json.JSONDecodeError:
                output = [{"raw": raw, "parse_error": True}]
            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id, success=True, output=output
            )
        except Exception as e:
            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id, success=False, output=None, error=str(e)
            )
