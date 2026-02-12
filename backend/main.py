"""
Granite - FastAPI Application

Exposes endpoints for async video generation:
  POST /api/generate     -> accepts PDF + description, returns job_id
  GET  /api/status/{id}  -> poll pipeline progress
  GET  /api/video/{id}   -> serve final video file
"""

import os
import shutil
import uuid
import threading
import traceback
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import uvicorn

from crew import GraniteCrew

load_dotenv()

app = FastAPI(
    title="Granite API",
    description="Automated educational video generation pipeline",
    version="1.0.0",
)

# Allow frontend to connect from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── In-memory job store ──────────────────────────────────────────────
# {
#   job_id: {
#     "status":       "processing" | "completed" | "failed",
#     "current_step": "extraction" | "planning" | "animation" | ...
#     "progress":     0-100,
#     "message":      "Human-readable status text",
#     "video_path":   "/abs/path/to/final.mp4" | None,
#     "error":        "Error message" | None,
#     "description":  "User's topic description",
#   }
# }
jobs: dict = {}

# Map CrewAI task indices to step names and progress percentages
PIPELINE_STEPS = [
    {"step": "extraction",  "label": "Extracting content",        "progress": 10},
    {"step": "planning",    "label": "Planning lesson structure",  "progress": 25},
    {"step": "animation",   "label": "Generating Manim animation","progress": 50},
    {"step": "narration",   "label": "Creating narration audio",  "progress": 70},
    {"step": "composition", "label": "Composing final video",     "progress": 85},
    {"step": "quality",     "label": "Quality checking",          "progress": 95},
]


def _make_task_callback(job_id: str):
    """Return a callback function that CrewAI will call after each task."""
    call_count = {"n": 0}  # mutable counter

    def callback(task_output):
        idx = call_count["n"]
        call_count["n"] += 1

        if job_id not in jobs:
            return
        if idx < len(PIPELINE_STEPS):
            step_info = PIPELINE_STEPS[idx]
            jobs[job_id]["current_step"] = step_info["step"]
            jobs[job_id]["progress"] = step_info["progress"]
            jobs[job_id]["message"] = f"{step_info['label']} — done ✓"
        # After the last step mark near-complete
        if idx >= len(PIPELINE_STEPS) - 1:
            jobs[job_id]["progress"] = 98
            jobs[job_id]["message"] = "Finalising output..."

    return callback


def _run_pipeline(job_id: str, file_path: Optional[str], description: str):
    """Run the Granite pipeline in a background thread."""
    try:
        # Build the prompt for the crew
        parts = []
        if file_path:
            parts.append(f"Extract and analyse the content from this file: {file_path}")
        if description:
            parts.append(f"Focus on explaining this concept: {description}")
        user_input = " ".join(parts) if parts else "General educational content"

        jobs[job_id]["message"] = "Initialising pipeline..."

        crew = GraniteCrew(
            topic=user_input,
            user_description=description,
            task_callback=_make_task_callback(job_id),
        )
        result = crew.run()

        # Try to extract video path from the result
        result_str = str(result)
        video_path = _extract_video_path(result_str, crew.job_dir)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["current_step"] = "done"
        jobs[job_id]["message"] = "Video generation complete!"
        jobs[job_id]["video_path"] = video_path

    except Exception as e:
        print(f"[Pipeline Error] Job {job_id}: {e}")
        traceback.print_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Pipeline error: {str(e)[:300]}"
        jobs[job_id]["error"] = str(e)


def _extract_video_path(result_str: str, job_dir: Path) -> Optional[str]:
    """Try to find the final .mp4 path from the pipeline result or job dir."""
    import re

    # 1. Try to extract a path from the result string
    mp4_match = re.search(r'([A-Za-z]:\\[^\s"\']+\.mp4|/[^\s"\']+\.mp4)', result_str)
    if mp4_match:
        candidate = mp4_match.group(1)
        if os.path.isfile(candidate):
            return candidate

    # 2. Search the job directory for mp4 files
    if job_dir.exists():
        mp4_files = list(job_dir.rglob("*.mp4"))
        if mp4_files:
            # Prefer "final" or "composed" in name, else the largest
            for f in mp4_files:
                if "final" in f.name.lower() or "composed" in f.name.lower():
                    return str(f)
            return str(max(mp4_files, key=lambda f: f.stat().st_size))

    # 3. Check the output_videos directory
    output_dir = Path("output_videos")
    if output_dir.exists():
        mp4_files = sorted(output_dir.rglob("*.mp4"), key=lambda f: f.stat().st_mtime, reverse=True)
        if mp4_files:
            return str(mp4_files[0])

    return None


# ── API Endpoints ────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Granite API is running.", "docs": "/docs"}


@app.post("/api/generate")
async def generate_video(
    file: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(None),
):
    """
    Start an async video generation job.

    - **file**: (optional) A PDF document to extract content from.
    - **description**: (optional) What the user wants to understand.

    Returns a job_id to poll for status.
    """
    if not file and not description:
        raise HTTPException(
            status_code=400,
            detail="Provide at least a file or a description.",
        )

    # Save uploaded file
    file_path = None
    if file:
        safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    # Create job
    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {
        "status": "processing",
        "current_step": "queued",
        "progress": 0,
        "message": "Job queued, starting pipeline...",
        "video_path": None,
        "error": None,
        "description": description or "",
    }

    # Launch pipeline in background thread
    thread = threading.Thread(
        target=_run_pipeline,
        args=(job_id, file_path, description or ""),
        daemon=True,
    )
    thread.start()

    return {"status": "accepted", "job_id": job_id}


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Poll pipeline progress for a given job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    return jobs[job_id]


@app.get("/api/video/{job_id}")
async def get_video(job_id: str):
    """Serve the final generated video."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")

    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Video not ready yet.")

    video_path = job.get("video_path")
    if not video_path or not os.path.isfile(video_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk.")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename="granite_output.mp4",
    )


# ── Serve frontend static files ─────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# ── Entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[
            "output_videos",
            "output_videos/*",
            "output_videos/**/*",
            "output",
            "output/*",
            "media",
            "uploads",
            "*.mp4",
            "*.mp3",
            "*.wav",
            "*.png",
            "*.log",
        ],
    )
