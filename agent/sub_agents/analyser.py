"""
AnalyserAgent — extracts structured signals from raw content.

Model: mistralai/Mistral-7B-Instruct-v0.3
Chosen for its strong instruction-following and reliable JSON output.
"""
import json
from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from agent.hf_client import hf_chat, extract_json_block


class AnalyserAgent(BaseAgent):
    agent_id = "analyser"
    capabilities = ["analyse"]
    model = "mistralai/Mistral-7B-Instruct-v0.3"

    _SYSTEM = (
        "You are a senior content strategist. "
        "You always respond with valid JSON only — no markdown, no explanation."
    )

    _PROMPT = """\
Analyse the provided content and return ONLY a valid JSON object with this exact structure:

{{
  "main_topic": "one-line description of the core topic",
  "key_themes": ["theme1", "theme2", "theme3"],
  "target_audiences": [
    {{"audience": "description", "why": "why this content suits them"}}
  ],
  "tone_of_source": "educational | conversational | technical | inspirational | controversial",
  "key_insights": ["insight1", "insight2", "insight3"],
  "content_angles": ["angle1", "angle2", "angle3"],
  "estimated_content_depth": "surface | intermediate | deep"
}}

Return ONLY the JSON object. No explanation, no markdown fences.

CONTENT:
{content}
"""

    def run(self, task: AgentTask) -> AgentResult:
        try:
            content = task.payload["content"]
            prompt = self._PROMPT.format(content=content[:12000])
            raw = hf_chat(self.model, prompt, max_tokens=1024, temperature=0.3, system=self._SYSTEM)
            try:
                output = json.loads(extract_json_block(raw))
            except json.JSONDecodeError:
                output = {"raw_analysis": raw, "parse_error": True}
            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id, success=True, output=output
            )
        except Exception as e:
            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id, success=False, output=None, error=str(e)
            )
