"""
Feedback routes.

POST /api/jobs/{id}/feedback   — submit a rating for one format's draft
GET  /api/jobs/{id}/feedback   — retrieve all feedback for a job
GET  /api/prompts/{format}     — list prompt version history for a format
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.db import get_job, create_feedback, get_feedback_for_job
from agent.prompt_store import get_prompt_store

router = APIRouter()


class FeedbackRequest(BaseModel):
    format: str = Field(..., pattern="^(linkedin|newsletter|instagram)$")
    rating: int = Field(..., ge=1, le=5)
    comment: str = ""


@router.post("/{job_id}/feedback", status_code=201)
async def submit_feedback(job_id: str, body: FeedbackRequest):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] != "done":
        raise HTTPException(400, "job must be in 'done' status to receive feedback")

    draft_text = job.get("drafts", {}).get(body.format)
    if not draft_text:
        raise HTTPException(400, f"no draft found for format '{body.format}'")

    prompt_version_id = job.get("prompt_versions_used", {}).get(body.format)

    fb = await create_feedback(
        job_id=job_id,
        format=body.format,
        rating=body.rating,
        comment=body.comment,
        draft_text=draft_text,
        prompt_version_id=prompt_version_id,
    )

    # Refresh avg_rating on the prompt version
    get_prompt_store().refresh_avg_rating(body.format)

    return {"feedback_id": fb["_id"], "rating": body.rating}


@router.get("/{job_id}/feedback")
async def get_feedback(job_id: str):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return await get_feedback_for_job(job_id)


@router.get("/prompts/{format}/versions")
async def get_prompt_versions(format: str):
    store = get_prompt_store()
    return store.list_versions(format)
