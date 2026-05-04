"""
PromptOptimizerAgent — rewrites drafter system prompts based on feedback patterns.

Triggered when MIN_FEEDBACKS unprocessed feedbacks accumulate for a format.
Samples high-rated and low-rated drafts, uses an LLM to identify patterns,
then creates a new active PromptVersion — preserving the full version history.

Model: mistralai/Mistral-7B-Instruct-v0.3
"""
import certifi
from pymongo import MongoClient

from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from agent.hf_client import hf_chat
from agent.prompt_store import get_prompt_store
from core.config import settings

MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
MIN_FEEDBACKS = 20
SAMPLE_SIZE = 5

_ANALYSIS_PROMPT = """\
You are a prompt engineer improving an AI content drafter.

Current system prompt for {fmt} drafts (version {version}):
---
{current_system}
---

High-rated drafts (users loved these, rated 4-5/5):
{high_examples}

Low-rated drafts (users disliked these, rated 1-2/5):
{low_examples}

Analyse what makes the high-rated drafts successful and what the low-rated ones lack.
Then write an improved system prompt that captures those success patterns.

Return ONLY the new system prompt text. No explanation, no preamble.
"""


class PromptOptimizerAgent(BaseAgent):
    agent_id = "prompt_optimizer"
    capabilities = ["optimize_prompt"]
    model = MODEL

    def run(self, task: AgentTask) -> AgentResult:
        fmt = task.payload["format"]
        min_fb = task.payload.get("min_feedbacks", MIN_FEEDBACKS)

        try:
            client = MongoClient(settings.mongodb_uri, tlsCAFile=certifi.where())
            feedback_col = client[settings.database_name].feedback

            unprocessed = list(feedback_col.find({"format": fmt, "processed": False}))
            if len(unprocessed) < min_fb:
                return AgentResult(
                    task_id=task.task_id, agent_id=self.agent_id,
                    success=True,
                    output={
                        "optimized": False,
                        "reason": f"{len(unprocessed)} feedbacks collected, {min_fb} needed",
                    },
                )

            store = get_prompt_store()
            current = store.get_active(fmt)
            if not current:
                return AgentResult(
                    task_id=task.task_id, agent_id=self.agent_id,
                    success=False, output=None,
                    error=f"No active prompt found for format '{fmt}'",
                )

            high = [f for f in unprocessed if f.get("rating", 0) >= 4][:SAMPLE_SIZE]
            low  = [f for f in unprocessed if f.get("rating", 0) <= 2][:SAMPLE_SIZE]

            def _fmt_examples(docs: list) -> str:
                if not docs:
                    return "(none available)"
                return "\n\n".join(
                    f"[Rating {d['rating']}/5]\n{d['draft_text'][:400]}" for d in docs
                )

            prompt = _ANALYSIS_PROMPT.format(
                fmt=fmt,
                version=current.version,
                current_system=current.system,
                high_examples=_fmt_examples(high),
                low_examples=_fmt_examples(low),
            )
            new_system = hf_chat(MODEL, prompt, max_tokens=600, temperature=0.3)

            new_version = store.create_version(fmt, new_system, current.template)

            # Mark feedbacks as processed
            ids = [f["_id"] for f in unprocessed]
            feedback_col.update_many(
                {"_id": {"$in": ids}}, {"$set": {"processed": True}}
            )

            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id,
                success=True,
                output={
                    "optimized": True,
                    "format": fmt,
                    "new_version": new_version.version,
                    "version_id": new_version.version_id,
                    "feedbacks_processed": len(unprocessed),
                },
            )
        except Exception as e:
            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id,
                success=False, output=None, error=str(e),
            )


