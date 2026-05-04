"""
Job queue routes.
POST /api/jobs          — submit a new job
GET  /api/jobs/{id}     — poll job status + results
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import json
from bson import ObjectId
from api.db import create_job, get_job, get_db

router = APIRouter()

@router.get("")
async def list_jobs():
    db = get_db()
    jobs = await db.jobs.find().sort("created_at", -1).to_list(100)
    for j in jobs:
        j["_id"] = str(j["_id"])
    return jobs


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


@router.get("/{job_id}/stream")
async def stream_job_updates(job_id: str):
    """
    Stream job status updates via SSE using MongoDB Change Streams.
    """
    async def event_generator():
        db = get_db()
        
        # 1. Yield initial state
        job = await get_job(job_id)
        if job:
            yield {"event": "status_update", "data": json.dumps(job, default=str)}
            if job["status"] in ["done", "failed", "awaiting_pick"]:
                return

        # 2. Watch for changes
        try:
            pipeline = [{"$match": {"documentKey._id": ObjectId(job_id)}}]
            async with db.jobs.watch(pipeline, full_document="updateLookup") as stream:
                async for change in stream:
                    updated_doc = change.get("fullDocument")
                    if updated_doc:
                        # Convert ObjectId to string for JSON serialization
                        updated_doc["_id"] = str(updated_doc["_id"])
                        yield {"event": "status_update", "data": json.dumps(updated_doc, default=str)}
                        if updated_doc["status"] in ["done", "failed", "awaiting_pick"]:
                            break
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())
