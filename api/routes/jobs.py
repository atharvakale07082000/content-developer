"""
Job queue routes.
POST /api/jobs          — submit a new job
GET  /api/jobs/{id}     — poll job status + results
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.db import create_job, get_job

router = APIRouter()


class JobRequest(BaseModel):
    input: str   # URL, YouTube link, or free-form topic


@router.post("", status_code=201)
async def submit_job(body: JobRequest):
    if not body.input.strip():
        raise HTTPException(400, "input must not be empty")
    job = await create_job(body.input.strip())
    return {"job_id": job["_id"], "status": job["status"]}


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job
