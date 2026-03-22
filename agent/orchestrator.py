"""
Orchestrator — the continuously running root agent.

Flow per job:
  1. Claim a pending job from MongoDB
  2. Detect input type → run the right tool to get raw content
  3. Analyser agent → structured analysis
  4. Suggester agent → ranked suggestions → write to DB (status: awaiting_pick)
  5. Poll until user picks formats (status: drafting)
  6. Run picked drafters in parallel → write drafts to DB (status: done)
  7. Sleep POLL_INTERVAL seconds → repeat
"""
import asyncio
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()

from core.config import settings

from api.db import (
    claim_next_pending_job,
    fail_job,
    get_job,
    set_drafts,
    set_suggestions,
)
from agent.tools.detect_input import detect_input_type
from agent.tools.youtube_tool import get_youtube_transcript
from agent.tools.scraper_tool import scrape_url
from agent.tools.topic_tool import expand_topic
from agent.sub_agents.analyser import analyse_content
from agent.sub_agents.suggester import generate_suggestions
from agent.sub_agents.drafters.linkedin import draft_linkedin
from agent.sub_agents.drafters.newsletter import draft_newsletter
from agent.sub_agents.drafters.instagram import draft_instagram

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

POLL_INTERVAL = settings.poll_interval_seconds
PICK_TIMEOUT  = 60 * 30  # 30 min — abandon job if user never picks

DRAFTER_MAP = {
    "linkedin":   draft_linkedin,
    "newsletter": draft_newsletter,
    "instagram":  draft_instagram,
}


# ── Step helpers ──────────────────────────────────────────────────────────────

def fetch_content(input_type: str, input_text: str) -> str:
    if input_type == "youtube":
        result = get_youtube_transcript(input_text)
        if not result["success"]:
            raise ValueError(f"YouTube fetch failed: {result['error']}")
        return result["transcript"]

    if input_type == "url":
        result = scrape_url(input_text)
        if not result["success"]:
            raise ValueError(f"Scrape failed: {result['error']}")
        title = result.get("title") or ""
        return f"{title}\n\n{result['text']}"

    # topic
    result = expand_topic(input_text)
    if not result["success"]:
        raise ValueError(f"Topic expansion failed: {result['error']}")
    return result["brief"]


def run_drafters_parallel(content: str, picked: list[str], suggestions: list) -> dict:
    """Run selected drafters concurrently using a thread pool."""
    # Pick the best matching suggestion per format (first match wins)
    suggestion_by_format = {}
    for fmt in picked:
        for s in suggestions:
            if s.get("format") == fmt:
                suggestion_by_format[fmt] = s
                break
        if fmt not in suggestion_by_format:
            suggestion_by_format[fmt] = {}   # fallback: empty suggestion

    def _draft(fmt: str) -> tuple[str, str]:
        drafter = DRAFTER_MAP[fmt]
        return fmt, drafter(content, suggestion_by_format[fmt])

    with ThreadPoolExecutor(max_workers=len(picked)) as pool:
        futures = {pool.submit(_draft, fmt): fmt for fmt in picked}
        drafts = {}
        for future in futures:
            fmt, text = future.result()
            drafts[fmt] = text
    return drafts


# ── Main loop ─────────────────────────────────────────────────────────────────

async def process_job(job: dict) -> None:
    job_id = job["_id"]
    log.info(f"Processing job {job_id}: {job['input'][:60]}")

    try:
        # 1. Detect + fetch content
        detection = detect_input_type(job["input"])
        input_type = detection["input_type"]
        log.info(f"  Input type: {input_type}")
        content = fetch_content(input_type, job["input"])

        # 2. Analyse
        analysis = analyse_content(content)
        log.info(f"  Analysis complete. Themes: {analysis.get('key_themes', [])[:2]}")

        # 3. Suggest
        suggestions = generate_suggestions(json.dumps(analysis))
        log.info(f"  Generated {len(suggestions)} suggestions")

        # 4. Write suggestions → status: awaiting_pick
        await set_suggestions(job_id, analysis, suggestions)
        log.info(f"  Job {job_id} → awaiting_pick")

        # 5. Poll for user pick (with timeout)
        deadline = time.time() + PICK_TIMEOUT
        while time.time() < deadline:
            await asyncio.sleep(5)
            updated = await get_job(job_id)
            if updated["status"] == "drafting":
                picked = updated["picked"]
                log.info(f"  User picked: {picked}")
                break
        else:
            await fail_job(job_id, "Timed out waiting for user to pick formats")
            return

        # 6. Draft in parallel
        drafts = run_drafters_parallel(content, picked, suggestions)
        await set_drafts(job_id, drafts)
        log.info(f"  Job {job_id} → done. Formats: {list(drafts.keys())}")

    except Exception as e:
        log.error(f"  Job {job_id} failed: {e}")
        await fail_job(job_id, str(e))


async def main():
    log.info(f"Content Strategy Agent started. Polling every {POLL_INTERVAL}s.")
    while True:
        job = await claim_next_pending_job()
        if job:
            await process_job(job)
        else:
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
