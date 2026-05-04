"""
RoutingAgent — central A2A router.

Builds the AgentRegistry at startup, then routes AgentTask instances to the
correct sub-agent based on task_type. The orchestrator calls two entry points:

  fetch_and_analyse(job_input)                        → (content, analysis, suggestions)
  run_pipeline(content, analysis, picked, sug.)       → (drafts, images, prompt_versions_used)
"""
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from agent.protocol import AgentTask, AgentResult
from agent.registry import AgentRegistry
from agent.sub_agents.content_fetcher import ContentFetcherAgent
from agent.sub_agents.analyser import AnalyserAgent
from agent.sub_agents.suggester import SuggesterAgent
from agent.sub_agents.drafters.linkedin import LinkedInDrafter
from agent.sub_agents.drafters.newsletter import NewsletterDrafter
from agent.sub_agents.drafters.instagram import InstagramDrafter
from agent.sub_agents.image_generator import ImageGeneratorAgent
from agent.sub_agents.feedback_retriever import FeedbackRetrieverAgent
from agent.sub_agents.prompt_optimizer import PromptOptimizerAgent

log = logging.getLogger(__name__)

_DRAFTER_TASK = {
    "linkedin":   "draft_linkedin",
    "newsletter": "draft_newsletter",
    "instagram":  "draft_instagram",
}


def _build_registry() -> AgentRegistry:
    registry = AgentRegistry()
    for agent in [
        ContentFetcherAgent(),
        AnalyserAgent(),
        SuggesterAgent(),
        LinkedInDrafter(),
        NewsletterDrafter(),
        InstagramDrafter(),
        ImageGeneratorAgent(),
        FeedbackRetrieverAgent(),
        PromptOptimizerAgent(),
    ]:
        registry.register(agent)
    return registry


class RoutingAgent:
    """
    Top-level A2A router. Decomposes a content job into typed AgentTasks
    and dispatches each one to the registered sub-agent for that capability.
    """

    def __init__(self):
        self._registry = _build_registry()
        log.info(
            "RoutingAgent ready. Registered agents: %s",
            [a["agent_id"] for a in self._registry.list_agents()],
        )

    # ── internal dispatch ──────────────────────────────────────────────────────

    def _dispatch(self, task: AgentTask) -> AgentResult:
        agent = self._registry.get_for_task(task.task_type)
        if agent is None:
            return AgentResult(
                task_id=task.task_id, agent_id="router",
                success=False, output=None,
                error=f"No agent registered for task type '{task.task_type}'",
            )
        log.info(
            "  → [%s] routing to '%s' (model: %s)",
            task.task_type, agent.agent_id, agent.model,
        )
        return agent.run(task)

    # ── public pipeline entry points ──────────────────────────────────────────

    def fetch_and_analyse(self, job_input: str) -> tuple[str, dict, list]:
        """
        Sequential pipeline: fetch content → analyse → suggest.
        Returns (content_str, analysis_dict, suggestions_list).
        """
        fetch_result = self._dispatch(AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="fetch_content",
            payload={"input_text": job_input},
        ))
        if not fetch_result.success:
            raise ValueError(f"ContentFetcher failed: {fetch_result.error}")
        content = fetch_result.output["content"]
        log.info("  Input type: %s", fetch_result.output["input_type"])

        analyse_result = self._dispatch(AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="analyse",
            payload={"content": content},
        ))
        if not analyse_result.success:
            raise ValueError(f"Analyser failed: {analyse_result.error}")
        analysis = analyse_result.output

        suggest_result = self._dispatch(AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="suggest",
            payload={"analysis": json.dumps(analysis)},
        ))
        if not suggest_result.success:
            raise ValueError(f"Suggester failed: {suggest_result.error}")

        return content, analysis, suggest_result.output

    def run_pipeline(
        self,
        content: str,
        analysis: dict,
        picked: list[str],
        suggestions: list,
    ) -> tuple[dict, dict, dict]:
        """
        Parallel stage: for each picked format —
          1. Fetch few-shot examples (FeedbackRetrieverAgent)
          2. Draft text (drafter agent)           ← parallel across formats
          3. Generate background image             ← parallel across formats
        Returns (drafts, images, prompt_versions_used).
        """
        # Pre-fetch few-shot examples per format (fast DB queries, done serially)
        few_shot_by_format: dict[str, str] = {}
        for fmt in picked:
            result = self._dispatch(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="retrieve_feedback",
                payload={"format": fmt, "top_k": 3},
            ))
            few_shot_by_format[fmt] = result.output.get("few_shot", "") if result.success else ""

        # Build suggestion lookup
        suggestion_by_format: dict = {}
        for fmt in picked:
            for s in suggestions:
                if s.get("format") == fmt:
                    suggestion_by_format[fmt] = s
                    break
            if fmt not in suggestion_by_format:
                suggestion_by_format[fmt] = {}

        def _draft(fmt: str) -> tuple[str, str, str, dict]:
            result = self._dispatch(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type=_DRAFTER_TASK[fmt],
                payload={
                    "content":    content,
                    "suggestion": suggestion_by_format[fmt],
                    "few_shot":   few_shot_by_format[fmt],
                },
            ))
            if not result.success:
                raise ValueError(f"Drafter '{fmt}' failed: {result.error}")
            return "draft", fmt, result.output, result.metadata

        def _image(fmt: str) -> tuple[str, str, str, dict]:
            result = self._dispatch(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="generate_image",
                payload={"analysis": analysis, "platform": fmt},
            ))
            if not result.success:
                log.warning("Image generation failed for '%s': %s", fmt, result.error)
                return "image", fmt, None, {}
            return "image", fmt, result.output["image_b64"], {}

        tasks = [(fn, fmt) for fmt in picked for fn in (_draft, _image)]
        drafts: dict = {}
        images: dict = {}
        prompt_versions_used: dict = {}

        with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            futures = [pool.submit(fn, fmt) for fn, fmt in tasks]
            for future in as_completed(futures):
                kind, fmt, output, meta = future.result()
                if kind == "draft":
                    drafts[fmt] = output
                    if meta.get("prompt_version_id"):
                        prompt_versions_used[fmt] = meta["prompt_version_id"]
                elif output is not None:
                    images[fmt] = output

        return drafts, images, prompt_versions_used

    def optimize_prompts(self, formats: list[str] | None = None) -> list[dict]:
        """
        Trigger PromptOptimizerAgent for each format.
        Called externally (e.g. a cron job or admin endpoint).
        """
        targets = formats or ["linkedin", "newsletter", "instagram"]
        results = []
        for fmt in targets:
            result = self._dispatch(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="optimize_prompt",
                payload={"format": fmt},
            ))
            results.append(result.output or {"format": fmt, "error": result.error})
        return results
