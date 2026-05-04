"""
PromptStore — MongoDB-backed prompt version registry.

Each drafter format has exactly one active PromptVersion at any time.
Versions are immutable once created; optimization creates a new version
and deactivates the previous one, preserving the full audit trail.

Sync pymongo client — safe to call from synchronous agent code.
In-memory cache (TTL: 5 min) avoids a DB round-trip on every draft.
"""
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import certifi
from bson import ObjectId
from pymongo import MongoClient

from core.config import settings

_CACHE_TTL = 300  # seconds


@dataclass
class PromptVersion:
    version_id: str
    format: str
    system: str
    template: str
    version: int


class PromptStore:
    def __init__(self):
        self._client = MongoClient(settings.mongodb_uri, tlsCAFile=certifi.where())
        self._col = self._client[settings.database_name].prompt_versions
        self._cache: dict[str, tuple[PromptVersion, float]] = {}

    def get_active(self, fmt: str) -> PromptVersion | None:
        cached, ts = self._cache.get(fmt, (None, 0))
        if cached and time.time() - ts < _CACHE_TTL:
            return cached
        doc = self._col.find_one({"format": fmt, "active": True})
        if not doc:
            return None
        pv = PromptVersion(
            version_id=str(doc["_id"]),
            format=fmt,
            system=doc["system"],
            template=doc["template"],
            version=doc["version"],
        )
        self._cache[fmt] = (pv, time.time())
        return pv

    def seed(self, fmt: str, system: str, template: str) -> PromptVersion:
        """Insert version 1 if no active prompt exists for this format."""
        existing = self._col.find_one({"format": fmt, "active": True})
        if existing:
            return self.get_active(fmt)
        doc = {
            "format": fmt,
            "system": system,
            "template": template,
            "version": 1,
            "active": True,
            "created_at": datetime.now(timezone.utc),
            "avg_rating": None,
            "usage_count": 0,
        }
        result = self._col.insert_one(doc)
        pv = PromptVersion(
            version_id=str(result.inserted_id),
            format=fmt, system=system, template=template, version=1,
        )
        self._cache[fmt] = (pv, time.time())
        return pv

    def create_version(self, fmt: str, system: str, template: str) -> PromptVersion:
        """Create a new active version, deactivating the current one."""
        current = self._col.find_one({"format": fmt, "active": True})
        next_ver = (current["version"] + 1) if current else 1
        self._col.update_many({"format": fmt, "active": True}, {"$set": {"active": False}})
        doc = {
            "format": fmt,
            "system": system,
            "template": template,
            "version": next_ver,
            "active": True,
            "created_at": datetime.now(timezone.utc),
            "avg_rating": None,
            "usage_count": 0,
        }
        result = self._col.insert_one(doc)
        pv = PromptVersion(
            version_id=str(result.inserted_id),
            format=fmt, system=system, template=template, version=next_ver,
        )
        self._cache[fmt] = (pv, time.time())
        return pv

    def increment_usage(self, version_id: str) -> None:
        self._col.update_one(
            {"_id": ObjectId(version_id)}, {"$inc": {"usage_count": 1}}
        )

    def refresh_avg_rating(self, fmt: str) -> None:
        doc = self._col.find_one({"format": fmt, "active": True})
        if not doc:
            return
        feedback_col = self._client[settings.database_name].feedback
        ratings = [r["rating"] for r in feedback_col.find(
            {"prompt_version_id": str(doc["_id"])}, {"rating": 1}
        )]
        if ratings:
            self._col.update_one(
                {"_id": doc["_id"]},
                {"$set": {"avg_rating": round(sum(ratings) / len(ratings), 2)}},
            )

    def list_versions(self, fmt: str) -> list[dict]:
        return [
            {**d, "_id": str(d["_id"])}
            for d in self._col.find({"format": fmt}, sort=[("version", -1)])
        ]


_store: PromptStore | None = None


def get_prompt_store() -> PromptStore:
    global _store
    if _store is None:
        _store = PromptStore()
    return _store
