"""
LinkedInDrafter — writes scroll-stopping LinkedIn posts.

Model: microsoft/Phi-3-mini-128k-instruct
Prompt loaded from PromptStore (seeded from defaults on first use).
Accepts optional few_shot examples from FeedbackRetrieverAgent.
"""
from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from agent.hf_client import hf_chat
from agent.prompt_store import get_prompt_store

FORMAT = "linkedin"

_DEFAULT_SYSTEM = (
    "You are an expert LinkedIn ghostwriter. "
    "Return only the post text, ready to copy-paste. No preamble, no commentary."
)

_DEFAULT_TEMPLATE = """\
{few_shot}Write a high-performing LinkedIn post based on the content brief and suggestion below.

Rules:
- Start with a bold hook (first line must stop the scroll)
- Use short paragraphs (1-3 lines max)
- Include a personal or relatable angle
- End with a clear call-to-action or thought-provoking question
- Add 3-5 relevant hashtags at the end
- Length: 150-300 words
- Tone: {tone_angle}
- Target audience: {target_audience}

CONTENT BRIEF:
{content}

SUGGESTED HOOK:
{hook}
"""


class LinkedInDrafter(BaseAgent):
    agent_id = "drafter_linkedin"
    capabilities = ["draft_linkedin"]
    model = "microsoft/Phi-3-mini-128k-instruct"

    def run(self, task: AgentTask) -> AgentResult:
        try:
            content    = task.payload["content"]
            suggestion = task.payload.get("suggestion", {})
            few_shot   = task.payload.get("few_shot", "")

            store = get_prompt_store()
            pv = store.get_active(FORMAT) or store.seed(FORMAT, _DEFAULT_SYSTEM, _DEFAULT_TEMPLATE)

            prompt = pv.template.format(
                few_shot=few_shot,
                tone_angle=suggestion.get("tone_angle", "professional"),
                target_audience=suggestion.get("target_audience", "professionals"),
                content=content[:6000],
                hook=suggestion.get("hook", ""),
            )
            store.increment_usage(pv.version_id)
            output = hf_chat(self.model, prompt, max_tokens=800, temperature=0.7, system=pv.system)

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
