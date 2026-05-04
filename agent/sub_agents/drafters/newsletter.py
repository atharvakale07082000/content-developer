"""
NewsletterDrafter — writes full email newsletter editions.

Model: mistralai/Mistral-7B-Instruct-v0.3
Prompt loaded from PromptStore (seeded from defaults on first use).
Accepts optional few_shot examples from FeedbackRetrieverAgent.
"""
from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from agent.hf_client import hf_chat
from agent.prompt_store import get_prompt_store

FORMAT = "newsletter"

_DEFAULT_SYSTEM = (
    "You are an expert email newsletter writer. "
    "Return the full newsletter with clear section labels. No preamble, no meta-commentary."
)

_DEFAULT_TEMPLATE = """\
{few_shot}Draft a newsletter edition based on the content brief below.

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

CONTENT BRIEF:
{content}

ANGLE:
{hook}
"""


class NewsletterDrafter(BaseAgent):
    agent_id = "drafter_newsletter"
    capabilities = ["draft_newsletter"]
    model = "mistralai/Mistral-7B-Instruct-v0.3"

    def run(self, task: AgentTask) -> AgentResult:
        try:
            content    = task.payload["content"]
            suggestion = task.payload.get("suggestion", {})
            few_shot   = task.payload.get("few_shot", "")

            store = get_prompt_store()
            pv = store.get_active(FORMAT) or store.seed(FORMAT, _DEFAULT_SYSTEM, _DEFAULT_TEMPLATE)

            prompt = pv.template.format(
                few_shot=few_shot,
                tone_angle=suggestion.get("tone_angle", "conversational"),
                target_audience=suggestion.get("target_audience", "subscribers"),
                content=content[:8000],
                hook=suggestion.get("hook", ""),
            )
            store.increment_usage(pv.version_id)
            output = hf_chat(self.model, prompt, max_tokens=1500, temperature=0.72, system=pv.system)

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
