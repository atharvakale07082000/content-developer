"""
FeedbackRetrieverAgent — retrieves top-rated drafts as few-shot examples.

Queries the feedback collection for high-rated drafts (≥4/5) of a given
format and formats them as a few-shot injection string for the drafter.
Falls back to empty string when no feedback exists yet.
"""
import certifi
from pymongo import MongoClient

from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from core.config import settings


class FeedbackRetrieverAgent(BaseAgent):
    agent_id = "feedback_retriever"
    capabilities = ["retrieve_feedback"]
    model = None  # DB-only — no model inference

    def run(self, task: AgentTask) -> AgentResult:
        fmt = task.payload["format"]
        top_k = task.payload.get("top_k", 3)

        try:
            client = MongoClient(settings.mongodb_uri, tlsCAFile=certifi.where())
            col = client[settings.database_name].feedback
            docs = list(col.find(
                {"format": fmt, "rating": {"$gte": 4}},
                sort=[("rating", -1), ("created_at", -1)],
                limit=top_k,
            ))

            if not docs:
                return AgentResult(
                    task_id=task.task_id, agent_id=self.agent_id,
                    success=True, output={"few_shot": ""},
                )

            examples = [
                f"Example {i} (rated {d['rating']}/5):\n{d['draft_text'][:600]}"
                for i, d in enumerate(docs, 1)
            ]
            few_shot = (
                "Here are examples of high-performing drafts that users rated highly. "
                "Use them as a reference for tone, structure, and style:\n\n"
                + "\n\n---\n\n".join(examples)
                + "\n\n---\n\n"
            )
            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id,
                success=True, output={"few_shot": few_shot},
            )
        except Exception as e:
            # Non-fatal — drafter proceeds without few-shot
            return AgentResult(
                task_id=task.task_id, agent_id=self.agent_id,
                success=True, output={"few_shot": ""},
            )
