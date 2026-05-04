"""
Orchestrator — continuously running root process.

Owns only the job-claim loop and DB state transitions.
All AI work is delegated to the RoutingAgent (A2A router).

Flow per job:
  1. Claim a pending job from MongoDB
  2-4. Router → fetch content, analyse, suggest → write to DB (status: awaiting_pick)
  5.   Poll until user picks formats (status: drafting)
  6.   Router → run drafters in parallel → write drafts to DB (status: done)
  7.   Sleep POLL_INTERVAL seconds → repeat
"""
import asyncio
import logging
import time

from dotenv import load_dotenv
load_dotenv()

from core.config import settings
from api.db import claim_next_pending_job, fail_job, get_job, set_drafts, set_suggestions
from agent.router import RoutingAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

POLL_INTERVAL = settings.poll_interval_seconds
PICK_TIMEOUT  = 60 * 30   # 30 min — abandon job if user never picks

_router = RoutingAgent()


async def process_job(job: dict) -> None:
    job_id = job["_id"]
    log.info("Processing job %s: %s", job_id, job["input"][:60])

    try:
        # Steps 1-3: fetch content → analyse → suggest
        content, analysis, suggestions = _router.fetch_and_analyse(job["input"])
        log.info("  Analysis complete. Themes: %s", analysis.get("key_themes", [])[:2])
        log.info("  Generated %d suggestions", len(suggestions))

        # Write suggestions → status: awaiting_pick
        await set_suggestions(job_id, analysis, suggestions)
        log.info("  Job %s → awaiting_pick", job_id)

        # Poll for user pick (with timeout)
        deadline = time.time() + PICK_TIMEOUT
        while time.time() < deadline:
            await asyncio.sleep(5)
            updated = await get_job(job_id)
            if updated["status"] == "drafting":
                picked = updated["picked"]
                log.info("  User picked: %s", picked)
                break
        else:
            await fail_job(job_id, "Timed out waiting for user to pick formats")
            return

        # Step 4: draft + generate images in parallel via router
        drafts, images, prompt_versions_used = _router.run_pipeline(content, analysis, picked, suggestions)
        await set_drafts(job_id, drafts, images=images or None, prompt_versions_used=prompt_versions_used or None)
        log.info("  Job %s → done. Formats: %s  Images: %s", job_id, list(drafts.keys()), list(images.keys()))

    except Exception as e:
        log.error("  Job %s failed: %s", job_id, e)
        await fail_job(job_id, str(e))


async def main():
    log.info("Content Strategy Agent started. Polling every %ds.", POLL_INTERVAL)
    while True:
        job = await claim_next_pending_job()
        if job:
            await process_job(job)
        else:
            await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
