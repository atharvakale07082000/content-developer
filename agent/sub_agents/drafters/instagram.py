"""
InstagramDrafter — writes scroll-stopping Instagram captions.

Model: google/gemma-2-2b-it
Prompt loaded from PromptStore (seeded from defaults on first use).
Accepts optional few_shot examples from FeedbackRetrieverAgent.
"""
from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from agent.hf_client import hf_chat
from agent.prompt_store import get_prompt_store

FORMAT = "instagram"

_DEFAULT_SYSTEM = (
    "You are an expert Instagram content strategist. "
    "Return only the caption and hashtags, ready to copy-paste. No preamble."
)

_DEFAULT_TEMPLATE = """\
{few_shot}Write a high-performing Instagram caption based on the content brief below.

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

CONTENT BRIEF:
{content}

HOOK IDEA:
{hook}
"""


class InstagramDrafter(BaseAgent):
    agent_id = "drafter_instagram"
    capabilities = ["draft_instagram"]
    model = "google/gemma-2-2b-it"

    def run(self, task: AgentTask) -> AgentResult:
        try:
            content    = task.payload["content"]
            suggestion = task.payload.get("suggestion", {})
            few_shot   = task.payload.get("few_shot", "")

            store = get_prompt_store()
            pv = store.get_active(FORMAT) or store.seed(FORMAT, _DEFAULT_SYSTEM, _DEFAULT_TEMPLATE)

            prompt = pv.template.format(
                few_shot=few_shot,
                tone_angle=suggestion.get("tone_angle", "inspiring"),
                target_audience=suggestion.get("target_audience", "general audience"),
                content=content[:5000],
                hook=suggestion.get("hook", ""),
            )
            store.increment_usage(pv.version_id)
            output = hf_chat(self.model, prompt, max_tokens=700, temperature=0.8, system=pv.system)

            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id,
                success=True, output=output,
                metadata={"prompt_version_id": pv.version_id, "prompt_version": pv.version},
            )
        except Exception as e:
            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id,
                success=False, output=None, error=str(e),
            )
