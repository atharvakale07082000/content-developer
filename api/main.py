"""
FastAPI entry point.
Mounts /api/jobs and /api/suggestions routes.
Serves the Stitch-generated frontend from /frontend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.routes.jobs import router as jobs_router
from api.routes.suggestions import router as suggestions_router
from api.routes.feedback import router as feedback_router
# from api.routes.export import router as export_router

app = FastAPI(title="Content Strategy Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router,        prefix="/api/jobs",    tags=["jobs"])
app.include_router(suggestions_router, prefix="/api/jobs",    tags=["suggestions"])
app.include_router(feedback_router,    prefix="/api/jobs",    tags=["feedback"])
# app.include_router(export_router,      prefix="/api/jobs", tags=["export"])


@app.get("/health")
async def health():
    return {"status": "ok"}


# Mount frontend LAST so the "/" catch-all doesn't shadow API routes
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path) and os.listdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
