"""
Suggestion pick route.
POST /api/jobs/{id}/pick — user selects which formats to draft
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
from api.db import get_job, set_picked

router = APIRouter()

VALID_FORMATS = {"linkedin", "newsletter", "instagram"}


class PickRequest(BaseModel):
    formats: list[str]   # e.g. ["linkedin", "instagram"]


@router.post("/{job_id}/pick")
async def pick_suggestions(job_id: str, body: PickRequest):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] != "awaiting_pick":
        raise HTTPException(409, f"job is in status '{job['status']}', expected 'awaiting_pick'")

    invalid = set(body.formats) - VALID_FORMATS
    if invalid:
        raise HTTPException(400, f"unknown formats: {invalid}. valid: {VALID_FORMATS}")
    if not body.formats:
        raise HTTPException(400, "pick at least one format")

    await set_picked(job_id, body.formats)
    return {"job_id": job_id, "status": "drafting", "picked": body.formats}
