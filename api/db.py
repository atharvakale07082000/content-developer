"""
MongoDB client using Motor (async).
Handles job queue CRUD and output storage.
"""
import os
from datetime import datetime, timezone
from typing import Optional
from pymongo import AsyncMongoClient, ReturnDocument
from bson import ObjectId
from core.config import settings
import certifi

MONGODB_URI = settings.mongodb_uri
MONGODB_DB  = settings.database_name

_client: Optional[AsyncMongoClient] = None


def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        _client = AsyncMongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    return _client


def get_db():
    return get_client()[MONGODB_DB]


# ── Job status lifecycle ──────────────────────────────────────────────────────
# pending → processing → awaiting_pick → drafting → done | failed

async def create_job(input_text: str) -> dict:
    """Insert a new job into the queue. Returns the created doc."""
    db = get_db()
    doc = {
        "input":        input_text,
        "input_type":   None,        # filled by orchestrator
        "status":       "pending",
        "analysis":     None,
        "suggestions":  None,
        "picked":       [],          # list of format keys user selected
        "drafts":             {},    # {format: draft_text}
        "images":             {},    # {format: base64_png}
        "prompt_versions_used": {},  # {format: prompt_version_id}
        "error":        None,
        "created_at":   datetime.now(timezone.utc),
        "updated_at":   datetime.now(timezone.utc),
    }
    result = await db.jobs.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


async def get_job(job_id: str) -> Optional[dict]:
    db = get_db()
    doc = await db.jobs.find_one({"_id": ObjectId(job_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def claim_next_pending_job() -> Optional[dict]:
    """Atomically claim the oldest pending job for processing."""
    db = get_db()
    doc = await db.jobs.find_one_and_update(
        {"status": "pending"},
        {"$set": {"status": "processing", "updated_at": datetime.now(timezone.utc)}},
        sort=[("created_at", 1)],
        return_document=ReturnDocument.AFTER,
    )
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def update_job(job_id: str, **fields) -> None:
    db = get_db()
    await db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {**fields, "updated_at": datetime.now(timezone.utc)}},
    )


async def set_suggestions(job_id: str, analysis: dict, suggestions: list) -> None:
    await update_job(
        job_id,
        analysis=analysis,
        suggestions=suggestions,
        status="awaiting_pick",
    )


async def set_picked(job_id: str, picked: list[str]) -> None:
    await update_job(job_id, picked=picked, status="drafting")


async def set_drafts(
    job_id: str,
    drafts: dict,
    images: dict | None = None,
    prompt_versions_used: dict | None = None,
) -> None:
    fields: dict = {"drafts": drafts, "status": "done"}
    if images:
        fields["images"] = images
    if prompt_versions_used:
        fields["prompt_versions_used"] = prompt_versions_used
    await update_job(job_id, **fields)


async def create_feedback(
    job_id: str,
    format: str,
    rating: int,
    comment: str,
    draft_text: str,
    prompt_version_id: str | None,
) -> dict:
    db = get_db()
    doc = {
        "job_id":            job_id,
        "format":            format,
        "rating":            rating,
        "comment":           comment,
        "draft_text":        draft_text,
        "prompt_version_id": prompt_version_id,
        "processed":         False,
        "created_at":        datetime.now(timezone.utc),
    }
    result = await db.feedback.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


async def get_feedback_for_job(job_id: str) -> list[dict]:
    db = get_db()
    docs = await db.feedback.find({"job_id": job_id}).to_list(100)
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


async def fail_job(job_id: str, error: str) -> None:
    await update_job(job_id, status="failed", error=error)
