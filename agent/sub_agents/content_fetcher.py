"""
ContentFetcherAgent — owns all input-fetching tools.

Tools:
  - detect_input_type  → classifies the raw input
  - get_youtube_transcript  → pulls transcript for YouTube URLs
  - scrape_url              → extracts article text from web URLs
  - expand_topic            → builds a research brief for free-form topics

Model: Qwen/Qwen2.5-72B-Instruct (used internally by expand_topic)
"""
from agent.base_agent import BaseAgent
from agent.protocol import AgentTask, AgentResult
from agent.tools.detect_input import detect_input_type
from agent.tools.youtube_tool import get_youtube_transcript
from agent.tools.scraper_tool import scrape_url
from agent.tools.topic_tool import expand_topic


class ContentFetcherAgent(BaseAgent):
    agent_id = "content_fetcher"
    capabilities = ["fetch_content"]
    model = "Qwen/Qwen2.5-72B-Instruct"     # used by expand_topic tool

    def run(self, task: AgentTask) -> AgentResult:
        try:
            input_text = task.payload["input_text"]
            detection = detect_input_type(input_text)
            input_type = detection["input_type"]

            if input_type == "youtube":
                result = get_youtube_transcript(input_text)
                if not result["success"]:
                    raise ValueError(f"YouTube fetch failed: {result['error']}")
                content = result["transcript"]

            elif input_type == "url":
                result = scrape_url(input_text)
                if not result["success"]:
                    raise ValueError(f"Scrape failed: {result['error']}")
                title = result.get("title") or ""
                content = f"{title}\n\n{result['text']}"

            else:  # topic
                result = expand_topic(input_text)
                if not result["success"]:
                    raise ValueError(f"Topic expansion failed: {result['error']}")
                content = result["brief"]

            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                output={"content": content, "input_type": input_type},
            )
        except Exception as e:
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                output=None,
                error=str(e),
            )
